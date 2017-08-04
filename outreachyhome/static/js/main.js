jQuery(document).ready(function($) {
    $(".scroll, .scroll-logo").click(function(event){
        event.preventDefault();
        $('html,body').animate({scrollTop:$(this.hash).offset().top - ($('#home').innerHeight() - $('#home').height()) + 10}, 500);
    });

    var aboveHeight = $('header').outerHeight();
    $(window).scroll(function(){
        $('.nav-container').addClass('fixed').css('top','0').next()
        .css('padding-top', '80px');
    });

    $('.participants-list').hide();
    $('.view-participants').click(function () {
        if( $('.participants-list').is(":hidden") ) {
            $('.participants-list').show(400);
            $('.view-participants').html("Close");
        } else {
            $('.view-participants').html("Find out who's participating in this round!");
            $('.participants-list').hide(400);
        }
    });
});

$(function() {
    var pull        = $('#pull');
    menu        = $('.nav');
    menuHeight  = menu.height();
    $(pull).on('click', function(e) {
        e.preventDefault();
        menu.slideToggle();
    });
});

$(window).resize(function(){
    var w = $(window).width();
    if(w > 720 && menu.is(':hidden')) {
        menu.removeAttr('style');
    }
});

$(function() {
    $('.nav li a, .scroll-logo').on('click',function(){
        $('.nav-collapse').collapse('hide');
    }); 
});
