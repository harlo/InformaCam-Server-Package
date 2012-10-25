<?php

	//ini_set('error_reporting', E_ALL);
	require_once('sag/Sag.php');
	require_once('config.php');
	
	$sag = new Sag();
	$sag->login('highsteppers','youAreNotAServerAdmin');
	
	if($sag === null)
		header('Location: redir.php');
	
	$GLOBALS = array(
		'sag' => $sag,
		'a_ok' => "A_OK",
		'fail' => "FAIL",
		'media_type' => array(
			'image' => 400,
			'video' => 401
		),
		'requirements' => array(
			'baseImage' => 1995,
			'pgpKeyEncoded' => 1996
		),
		'supporting_data_types' => array(
			'baseImage' => 'baseImage.jpg',
			'publicKeyEncoded' => 'publicKey.asc'
		),
		'submission_root' => $submission_root,
		'root' => $root,
		'source_root' => $source_root,
		'derivative_root' => $derivative_root
	);
	
	function toErr($errno, $errstr) {
		echo $errno . ": " . $errstr . "<br />";
	}
	
	//set_error_handler('toErr');
	
	function isValidAuthTokenForUser($pgpKeyFingerprint, $auth_token, $db) {
		$uLog = $db->get("_design/submissions/_view/sourceId")->body->rows;
		if(count($uLog) == 0)
			return null;
		else {
			for($l = 0; $l < count($uLog); $l++) {
				if($uLog[$l]->value->auth_token == $auth_token) {
					return $uLog[$l]->value;
				}
			}	
		}
		return null;
	}
	
	function isValidImportForUser($pgpKeyFingerprint, $id, $rev, $db) {
		$uLog = $db->get("_design/submissions/_view/sourceId")->body->rows;
		if(count($uLog) == 0)
			return null;
		else {
			for($l = 0; $l < count($uLog); $l++) {
				if($uLog[$l]->value->_id == $id && $uLog[$l]->value->_rev == $rev) {
					return $uLog[$l]->value;
				}
			}
		}
	}
	
	function initSource($pgpKeyFingerprint, $db) {
		mkdir($GLOBALS['source_root'] . $pgpKeyFingerprint, 0770, true);
		$newSource = new stdclass;	
		$newSource->sourceId = $pgpKeyFingerprint;
				
		try {
			$db->post($newSource);
			return $newSource;
		} catch(SagException $e) {
			return null;
		}
	}
	
	function sourceExists($pgpKeyFingerprint, $db) {
		try {
			$uLog = $db->get("_design/sources/_view/sourceId?key=%22" . $pgpKeyFingerprint . "%22")->body->rows;
			if(count($uLog) == 0) {
				return null;
			} else {
				return $uLog[0]->value;
			}
		} catch(SagException $e) {
			echo $e->getMessage();
			return null;
		}
	}
	
	class InformaMessage {
		private $expectation;
		protected $sag;
		public $res;
		
		
		public function __construct($base, $pgpKeyFingerprint, $msg) {
			$this->res = new stdclass;
			$this->res->result = $GLOBALS['fail'];
					
			$this->sag = $GLOBALS['sag'];
			$this->sag->setDatabase('sources');
			$this->expectation = sourceExists($pgpKeyFingerprint, $this->sag);
			
			if($this->expectation == null) {
				$this->res->reason = "No source exists for " . $pgpKeyFingerprint;
				return;
			}
			

			if(!move_uploaded_file(
				$msg['tmp_name'],
				$GLOBALS['derivative_root'] . $base . "/messages/" . basename($msg['name']))
			) {
				$this->res->reason = "Trouble uploading file.";
				$this->res->error_code = 1999;
				return;
			}
			
			$this->res->result = $GLOBALS['a_ok'];
		}

	}
	
	class Messages {
		private $expectation;
		protected $sag;
		public $res;
		
		public function __construct($mediaBase, $pgpKeyFingerprint, $readArrayStr) {
			$this->res = new stdclass;
			$this->res->result = $GLOBALS['fail'];
			
			$this->sag = $GLOBALS['sag'];
			$this->sag->setDatabase('sources');
			$this->expectation = sourceExists($pgpKeyFingerprint, $this->sag);
			
			if($this->expectation == null) {
				$this->res->reason = "No source exists for " . $pgpKeyFingerprint;
				return;
			}
			
			if($readArrayStr != null)
				$readArray = explode('","', substr($readArrayStr,2,-2));
			
			$msgRoot = $GLOBALS['derivative_root'] . $mediaBase . "/messages/";			
			$messages = scandir($msgRoot);
			$unread = array();
			foreach($messages as $msg) {
				if($msg != "." && $msg != "..") {
					if($readArray != null && in_array($msg, $readArray)) {
						continue;
					}
					
					$message = new stdclass;
					$message->url = $msg;
					$m = fopen($msgRoot . $msg, "r");
					while(!feof($m))
						$message->content .= fgets($m);
					fclose($m);
					array_push($unread, $message);

				}
			}
			
			if(count($unread) > 0) {
				$this->res->bundle->messages = $unread;
			}
			
			$this->res->result = $GLOBALS['a_ok'];
			
		}
	}
	
	class UploadCheck {
		private $expectation;
		protected $sag;
		public $res;
		
		public function __construct($j3mBase, $pgpKeyFingerprint, $auth_token) {
			$this->res = new stdclass;
			$this->res->result = $GLOBALS['fail'];
			
			$this->sag = $GLOBALS['sag'];
			$this->sag->setDatabase('submissions');
			
			$this->expectation = isValidAuthTokenForUser($pgpKeyFingerprint, $auth_token, $this->sag);
			
			if($this->expectation === null) {
				$this->res->reason = "Invalid auth token for user.";
				$this->res->error_code = 1998;
				return;
			}
			
			$c = $this->expectation->j3m->num_chunks;
			$files = scandir($GLOBALS['submission_root'] . $j3mBase);
			$missing = array();

			foreach(range(0, $c-1) as $check) {
				$f = $check . "_.j3mtorrent";
				
				if(!in_array($f, $files))
					array_push($missing, $check);
				
			}
			
			if(count($missing) == 0) {
				$this->res->reason = "No files are missing";
				$this->res->error_code = 1997;
				return;
			}
			
			$this->res->result = $GLOBALS['a_ok'];
			$this->res->missingTorrents = $missing;
		}
	}
	
	class RequirementCheck {
		private $expectation;
		protected $sag;
		public $res;
		
		public function __construct($pgpKeyFingerprint) {
			$this->res = new stdclass;
			$this->res->result = $GLOBALS['fail'];
		
			$this->sag = $GLOBALS['sag'];
			$this->sag->setDatabase('sources');
			$this->expectation = sourceExists($pgpKeyFingerprint, $this->sag);
			
			$requirements = array();
			
			if($this->expectation == null) {
				$this->expectation = initSource($pgpKeyFingerprint, $this->sag);
				$requirements = array(
					$GLOBALS['requirements']['baseImage'],
					$GLOBALS['requirements']['pgpKeyEncoded']
				);
				
			} else {
				$files = scandir($GLOBALS['source_root'] . $pgpKeyFingerprint);
				if(!in_array($GLOBALS['supporting_data_types']['baseImage'], $files))
					array_push($requirements, $GLOBALS['requirements']['baseImage']);
						
				if(!in_array($GLOBALS['supporting_data_types']['publicKeyEncoded'], $files))
					array_push($requirements, $GLOBALS['requirements']['pgpKeyEncoded']);
			}
			
			if(count($requirements) > 0)
				$this->res->bundle->requirements = $requirements;
				
			$this->res->result = $GLOBALS['a_ok'];
		}
	}
	
	class MediaUploader {
		private $expectation;
		protected $sag;
		public $res;
		
		public function __construct($pgpKeyFingerprint, $auth_token, $file) {
			$this->res = new stdclass;
			$this->res->result = $GLOBALS['fail'];
						
			$this->sag = $GLOBALS['sag'];
			$this->sag->setDatabase('submissions');
			
			$this->expectation = isValidAuthTokenForUser($pgpKeyFingerprint, $auth_token, $this->sag);
			
			if($this->expectation === null) {
				$this->res->reason = "Invalid auth token for user.";
				$this->res->error_code = 1998;
				return;
			}
			
			if(file_exists($GLOBALS['submission_root'] . $this->expectation->j3m->originalHash . "/" . basename($file['name']))) {
				$this->res->reason = "already have file";
				$this->res->error_code = 2000;
				return;
			}
			
			if(!move_uploaded_file(
				$file['tmp_name'],
				$GLOBALS['submission_root'] . $this->expectation->j3m->originalHash . "/" . basename($file['name']))
			) {
				$this->res->reason = "Trouble uploading file.";
				$this->res->error_code = 1999;
				return;
			}
			
			$newSize = $this->expectation->bytes_transferred + $file['size'];
			$this->expectation->bytes_transferred = $newSize;
			
			if($this->expectation->j3m != null) {
				if($newSize == $this->expectation->j3m_bytes_expected) {
					unset($this->expectation->auth_token);
				}
			} else {
				if($newSize == $this->expectation->bytes_expected) {
					unset($this->expectation->auth_token);
				}
			}
			
			$this->sag->post($this->expectation);
			
			$this->res->result = $GLOBALS['a_ok'];
			$this->res->bundle = $this->expectation;
		}
	}
	
	class UploadScheduler {
		private $bundle, $jDump;

		protected $sag;
		public $res;
		
		public function __construct($j3m) {
			$timestamp_scheduled = time() * 1000;
			
			$j3m = json_decode(stripslashes($j3m));
			$this->bundle = new stdclass;
			
			$this->bundle->timestamp_scheduled = $timestamp_scheduled;
			$this->bundle->timestamp_created = $j3m->timestampCreated;
			$this->bundle->sourceId = $j3m->pgpKeyFingerprint;
			$this->bundle->bytes_transferred = 0;
			$this->bundle->bytes_expected = $j3m->totalBytesExpected;
			$this->bundle->j3m_bytes_expected = $j3m->j3mBytesExpected;
			$this->bundle->mediaType = $j3m->mediaType;
			$this->bundle->j3m = $j3m;
			
			
			$this->res = new stdclass;
			$this->res->result = $GLOBALS['fail'];
			
			$file = fopen('authCache/cache.json','r');
			$dump = "";
			while(!feof($file))
				$dump .= fgets($file);
			fclose($file);
			$this->jDump = json_decode($dump);
			
			$this->bundle->auth_token = $this->generateAuthToken();
			unset($this->jDump);
			
			if(!mkdir($GLOBALS['submission_root'] . $j3m->originalHash, 0770, true)) {
				$this->res->reason = "Cannot create directory for " . $GLOBALS['submission_root'] . $j3m->originalHash;
				return;
			}
			$this->bundle->path = $GLOBALS['submission_root'] . $j3m->originalHash;
						
			$this->sag = $GLOBALS['sag'];
			$this->sag->setDatabase('submissions');
			
			try {
				$this->sag->post($this->bundle);
				unset($this->bundle->path);
				
				$this->sag->setDatabase('sources');
				$source = sourceExists($this->bundle->sourceId, $this->sag);
				$supportingDataRequired = array();
				
				if($source == null) {
					// also ask for missing req. files
					$source = initSource($this->bundle->sourceId, $this->sag);
					$supportingDataRequired = array(
						$GLOBALS['requirements']['baseImage'],
						$GLOBALS['requirements']['pgpKeyEncoded']
					);
				} else {
					// check to see if there are missing req. files
					$requirementCheck = new RequirementCheck($this->bundle->sourceId);
					if($requirementCheck->res->result == $GLOBALS['a_ok'] && isset($requirementCheck->bundle->requirements)) {
						$supportingDataRequired = $requirementCheck->bundle->requirements;
					}
				}
				
				if(count($supportingDataRequired) > 0)
					$this->bundle->supportingDataRequired = $supportingDataRequired;
				
				$this->res->bundle = $this->bundle;
				$this->res->result = $GLOBALS['a_ok'];
			} catch(SagException $e) {
				$this->result->reason = $e->getMessage();
				return;
			}
			
			$this->res->bundle = $this->bundle;
			unset($this->res->bundle->j3m);
			
			$this->res->result = $GLOBALS['a_ok'];
		}
		
		private function strep($str, $len) {
			$str = preg_replace('/[^a-zA-Z-,\s]/', "", $str);
			$str = str_replace(" ", "", $str);
			$str = str_replace(",", "", $str);
			$str = str_replace("\\", "", $str);
			$str = str_replace("\\n", "", $str);
			$str = str_replace("%", "", $str);
			return substr($str, 0, $len);
		}
		
		private function generateAuthToken() {
			$p1 = rand(0, count($this->jDump) - 1);
			$p2 = $p3 = -1;
			$at = $this->strep($this->jDump[$p1]->text, rand(0, 50));
			
			do {
				$p2 = rand(0, count($this->jDump) - 1);
			} while($p2 == $p1);
			$at .= $this->strep($this->jDump[$p2]->text, rand(0, 60));
			
			do {
				$p3 = rand(0, count($this->jDump) - 1);
			} while($p3 == $p1 || $p3 == $p2);
			$at .= $this->strep($this->jDump[$p3]->text, rand(0, 50));
			
			return $at;
		}
	}
		
	class SupportingDataUpload {
		private $expectation;
		protected $sag;
		public $res;
		
		public function __construct($supportingDataType, $pgpKeyFingerprint, $file) {
			
			$this->res = new stdclass;
			$this->res->result = $GLOBALS['fail'];
			
			$this->sag = $GLOBALS['sag'];
			$this->sag->setDatabase('sources');
			
			$this->expectation = sourceExists($pgpKeyFingerprint, $this->sag);
			if($this->expectation == null) {
				$this->res->reason = "No source exists for " . $pgpKeyFingerprint;
				return;
			}
			
			
			if(file_exists($GLOBALS['source_root'] . basename($file['name']))) {
				$this->res->reason = "File exists: " . basename($file['name']);
				return;
			}
			
			
			if(!move_uploaded_file(
				$file['tmp_name'],
				$GLOBALS['source_root'] . basename($file['name'])
				)
			) {
				$this->res->reason = "Could not upload file: " . basename($file['name']);
				return;
			}
			
			if($supportingDataType == $GLOBALS['supporting_data_types']['baseImage']) {
				$this->expectation->baseImage = $GLOBALS['source_root'] . basename($file['name']);
			} else if($supportingDataType == $GLOBALS['supporting_data_types']['publicKeyEncoded']) {
				$this->expectation->publicKeyEncoded = $GLOBALS['source_root'] . basename($file['name']);
			}
			
			
			try {
				$this->sag->post($this->expectation);
				$this->res->result = $GLOBALS['a_ok'];
			} catch(SagException $e) {
				$this->res->reason = $e.getMessage();
				return;
			}
					
		}
	}
	
	if(
		!empty($_POST['pgpKeyFingerprint']) &&
		!empty($_POST['auth_token']) &&
		!empty($_FILES['InformaCamUpload'])
	) {		
		$uploader = new MediaUploader(
			$_POST['pgpKeyFingerprint'],
			$_POST['auth_token'],
			$_FILES['InformaCamUpload']
		);
		
		echo json_encode($uploader->res);
	}
	
	if(!empty($_GET['j3m'])) {
		$uploadScheduler = new UploadScheduler($_GET['j3m']);
		echo json_encode($uploadScheduler);
	}
	
	if(!empty($_POST['j3m'])) {
		$uploadScheduler = new UploadScheduler($_POST['j3m']);
		echo json_encode($uploadScheduler);
	}
	
	if(!empty($_POST['hello'])) {
		echo "hello yourself!";
	}
	
	if(!empty($_GET['hello'])) {
		echo "hello yourself!";
	}
	
	if(
		!empty($_POST['checkForMissingTorrents']) &&
		!empty($_POST['pgpKeyFingerprint']) &&
		!empty($_POST['auth_token'])
	) {
		// check for missing uploads
		$uploadCheck = new UploadCheck(
			$_POST['checkForMissingTorrents'],
			$_POST['pgpKeyFingerprint'],
			$_POST['auth_token']
		);
		echo json_encode($uploadCheck);
	}
	
	if(
		!empty($_POST['supportingData']) &&
		!empty($_POST['pgpKeyFingerprint']) &&
		!empty($_FILES['InformaCamUpload'])
	) {
		// TODO: upload supporting data
		$supportingDataUpload = new SupportingDataUpload(
			$_POST['supportingData'],
			$_POST['pgpKeyFingerprint'],
			$_FILES['InformaCamUpload']
		);
		echo json_encode($supportingDataUpload);
	}
	
	if(
		!empty($_POST['getRequirements']) 
	) {
		// get supporting data required for source (pgp key, base image)
		$requirementCheck = new RequirementCheck($_POST['getRequirements']);
		echo json_encode($requirementCheck);
	}
	
	if(
		!empty($_GET['getRequirements']) 
	) {
		// get supporting data required for source (pgp key, base image)
		$requirementCheck = new RequirementCheck($_GET['getRequirements']);
		echo json_encode($requirementCheck);
	}
	
	if(
		!empty($_GET['getMessages']) &&
		!empty($_GET['pgpKeyFingerprint'])
	) {
		$messages = new Messages($_GET['getMessages'],$_GET['pgpKeyFingerprint'],empty($_GET['readArray']) ? null : $_GET['readArray']);
		echo json_encode($messages);
		// getMessages=cb662bb1389dbe16a9dbb6f36b83d3198a289c78&pgpKeyFingerprint=04e29577e1db4af33027c0db61ce70a6604b585f&readArray=[]
	}
	
	if(
		!empty($_POST['getMessages']) &&
		!empty($_POST['pgpKeyFingerprint'])
	) {
		$messages = new Messages($_POST['getMessages'],$_POST['pgpKeyFingerprint'],empty($_POST['readArray']) ? null : $_POST['readArray']);
		echo json_encode($messages);
		// getMessages=cb662bb1389dbe16a9dbb6f36b83d3198a289c78&pgpKeyFingerprint=04e29577e1db4af33027c0db61ce70a6604b585f&readArray=[]
	}
	

	if(
		!empty($_POST['putNewMessage']) &&
		!empty($_POST['pgpKeyFingerprint']) &&
		!empty($_FILES['InformaCamUpload'])
	) {
		
		$message = new InformaMessage(
			$_POST['putNewMessage'],
			$_POST['pgpKeyFingerprint'],
			$_FILES['InformaCamUpload']
		);
		echo json_encode($message);
	}
	
	class Importer {
		protected $sag;
		private $expectation;
		public $res;
		
		public function __construct($file, $rev, $id, $uId) {
			$this->res = new stdclass;
			$this->res->result = $GLOBALS['fail'];
			
			// hash the media
			$timestamp_scheduled = time() * 1000;
			$original_hash = hash("sha1", $file['name'] . $timestamp_scheduled);
			
			// make its folders and whatever
			if(!mkdir($GLOBALS['submission_root'] . $original_hash, 0770, true)) {
				$this->res->reason = "Cannot create directory for " . $GLOBALS['submission_root'] . $original_hash;
				return;
			}
			
			// place in there
			if(!move_uploaded_file(
				$file['tmp_name'],
				$GLOBALS['submission_root'] . $original_hash . "/" . basename($file['name'])
				)
			) {
				$this->res->reason = "Could not upload file: " . $GLOBALS['submission_root'] . $original_hash . "/" . basename($file['name']);
				return;
			}
			
			$this->sag = $GLOBALS['sag'];
			$this->sag->setDatabase('submissions');
			
			$this->expectation = null;
			try {
				$this->expectation = isValidImportForUser($uId, $id, $rev, $this->sag);
			} catch(SagException $e) {
				$this->res->reason = $e->getMessage();
				return;
			}
			
			if($this->expectation == null) {
				$this->res->reason = "Invalid id/rev";
				return;
			}
			
			
			// update sub to have path and media type, update all bytes transferred, and set a flag for complete ul?
			
			$this->expectation->path = $GLOBALS['submission_root'] . $original_hash . "/" . basename($file['name']);
			
			if(strpos($file['name'], ".jpg"))
				$this->expectation->mediaType = 400;
			else if(strpos($file['name'], ".mkv"))
				$this->expectation->mediaType = 401;
				
			$this->expectation->bytes_transferred = $file['size'];
			$this->expectation->bytes_expected = $file['size'];
			$this->expectation->j3m_bytes_expected = $file['size'];
			$this->expectation->importFlag = true;
			$this->expectation->timestamp_scheduled = $timestamp_scheduled;
			
			try {
				$this->sag->post($this->expectation);
			} catch(SagException $e) {
				$this->result->reason = $e->getMessage();
				return;
			}
			
			$this->res->result = $GLOBALS['a_ok'];
		}
	}
	
	if(
		!empty($_FILES['InformaCamImport']) &&
		!empty($_POST['subAuthToken']) &&
		!empty($_POST['subId']) &&
		!empty($_POST['uId'])
	) {
		$import = new Importer($_FILES['InformaCamImport'], $_POST['subAuthToken'], $_POST['subId'], $_POST['uId']);
		// TODO: parse result...
		include('doImport.php');
		
	}
	
	if(!empty($_GET['doImport'])) {
		include('doImport.php');
	}

	/*
	foreach($_POST as $p=>$v) {
		echo $p . " = " . $v . ";";
	}
	
	foreach($_FILES as $f) {
		echo "a file: ";
		foreach($f as $p=>$v)
			echo $p . " = " . $v . ";";
	}
	*/
?>