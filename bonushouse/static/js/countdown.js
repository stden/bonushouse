function countDown(block) {
    days = parseInt($('.days', block).text());
    hours = $('.hours', block).text();
    minutes = $('.minutes', block).text();
    seconds = $('.seconds', block).text();
    if(seconds[0] == '0') {
        seconds = seconds.substring(1);
    }
    if(minutes[0] == '0') {
        minutes = minutes.substring(1);
    }
    if(hours[0] == '0') {
        hours = hours.substring(1);
    }
    seconds = parseInt(seconds);
    minutes = parseInt(minutes);
    hours = parseInt(hours);
    seconds -= 1;
    if(seconds < 0) {
        minutes -= 1;
        seconds = 59;
    }
    if(minutes < 0) {
        hours -= 1;
        minutes = 59;
    }
    if(hours < 0) {
        days -= 1;
        hours = 23;
    }
    if(days < 0) {
        $('.days', block).text(0);
        $('.hours', block).text(0);
        $('.minutes', block).text(0);
        $('.seconds', block).text(0);
        return;
    }
    else {
        if(hours<10) {
            hours = '0'+(hours+'');
        }
        if(minutes<10) {
            minutes = '0'+(minutes+"");
        }
        if(seconds<10) {
            seconds = '0'+(seconds+'');
        }
        $('.days', block).text(days);
        $('.hours', block).text(hours);
        $('.minutes', block).text(minutes);
        $('.seconds', block).text(seconds);
        setTimeout(function() {
            countDown(block);
        }, 1000)
    }
}