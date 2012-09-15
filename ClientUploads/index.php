<?php

	ini_set('error_reporting', E_ALL);
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
		'submission_root' => $submission_root,
		'root' => $root
	);
	
	function toErr($errno, $errstr) {
		echo $errno . ": " . $errstr;
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
		//TODO: check for missing uploads
		$uploadCheck = new UploadCheck(
			$_POST['checkForMissingTorrents'],
			$_POST['pgpKeyFingerprint'],
			$_POST['auth_token']
		);
		echo json_encode($uploadCheck);
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