$(function() {

	$('.reload_captcha').click(function() {
		var captcha = $(this).parents('div.captcha');

		$.getJSON('/captcha/refresh/', {}, function(json) {
			$('#id_captcha_0', captcha).val(json.key);
			$('img', captcha).attr('src', json.image_url);
		});

		return false;
	});

	$('.audio_captcha').click(
			function() {
				var captcha = $(this).parents('div.captcha');
				window.open('/captcha/audio/' +
						$('#id_captcha_0', captcha).val() + '/');
			});

});