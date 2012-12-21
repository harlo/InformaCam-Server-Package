<?php

if(!empty($_GET['fileData']) && !empty($_GET['sourceId'])) {
	header('Content-disposition: attachment; filename=' . $_GET['sourceId'] . '.ictd');
	header('Content-type: application/octet-stream');
	readfile($_GET['fileData']);
}
?>
