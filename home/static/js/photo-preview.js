// Code snippet from https://stackoverflow.com/questions/4459379/preview-an-image-before-it-is-uploaded
function readURL(input) {
	if (input.files && input.files[0]) {
		var reader = new FileReader();
            
		reader.onload = function (e) {
			$('#blah').attr('src', e.target.result);
		}

		reader.readAsDataURL(input.files[0]);
	}
}
    
$("#imgInp").change(function(){
	readURL(this);
});
