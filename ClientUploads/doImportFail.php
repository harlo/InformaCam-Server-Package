<html>
	<head>
		<title>importer</title>
		<style>
			body {
				font-family:arial;
				margin:0;
				padding:0;
				overflow:hidden;
				font-size:24px;
				color:#444;
				background-color:#0a5587;
				border:1px solid #c6ff00;
				box-shadow:4px 4px 8px;
			}
			
			h1 {
				background-color:#c6ff00;
				color:#8fae22;
				font-weight:normal;
				font-size:0.65em;
				margin:0 0 10px 0;
				padding:8px;
				text-align:left;
				text-transform:uppercase;
			}
			
			p {
				color:#fff;
				font-size:0.65em;
				margin:5px 10px;
			}
			
			input {
				margin:5px 10px;
			}
			
			input.ic_submit {
				background-color:#8fae22;
				color:#fff;
				padding:4px 10px;
				border:none;
				float:right;
				cursor:pointer;
			}
			
			input.ic_browse {
				width:auto;
			}
			
			a.dismiss, a.dismiss:link, a.dismiss:visited, a.dismiss:hover {
				background-color:#8fae22;
				color:#fff;
				padding:4px 10px;
				border:none;
				cursor:pointer;
			}
		</style>
		<script type="text/javascript">
			function listener() {
				document.getElementsByTagName('body')[0].style.display = "none";
			}
			
			function validateForm() {
				var file = document.getElementById('InformaCamImport');
				if(!/(\.jpg|\.mkv)$/i.test(file.value)) {
					return false;
				}
				return true;
			}
		</script>
	</head>
	
	<body>
		<h1>Import Media Fail</h1>
		<p>Sorry, media upload has failed.  Please try again.<br /><br /><a class="dismiss" onclick="listener();">OK</a></p>
	</body>
</html>