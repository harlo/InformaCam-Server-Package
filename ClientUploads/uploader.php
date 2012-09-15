<?php

?>
<html>
	<head>
		<title>upload to me!</title>
	</head>
	<body>
		<form enctype="multipart/form-data" action="index.php" method="post">
			<table>
				<tr>
					<td>auth_token:</td>
					<td><input type="text" name="auth_token" /></td>
				</tr>
				<tr>
					<td>pgpKeyFingerprint:</td>
					<td><input type="text" name="pgpKeyFingerprint" /></td>
				</tr>
				<tr>
					<td>file:</td>
					<td><input type="file" name="InformaCamUpload" /></td>
				</tr>
				<tr>
					<td colspan="2"><input type="submit" value="upload" /></td>
				</tr>
			</table>
		</form>
	</body>
</html>