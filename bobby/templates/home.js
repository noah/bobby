$(function() {

    var board = ChessBoard('board', {
        'position'      : 'start',
        'pieceTheme'    : '/static/img/chesspieces/wikipedia/{piece}.png'
    });

    var counter_w, counter_b;
    var remain_w, remain_b;
    var timer_w = function() {
        if(remain_w < 0) {
            clearInterval(remain_w); clearInterval(remain_b); return;
        }
        remain_w-=4;
        $('#white_time_remain').html(remain_w/1000);
    };
    var timer_b = function() {
        if(remain_b < 0) { 
            clearInterval(remain_w); clearInterval(remain_b); return;
        }
        remain_b-=4;
        $('#black_time_remain').html(remain_b/1000);
    };


    var override = {
        'orientation' : function(data) {
            board.orientation(data.orientation);
        },
        'fen' : function(data) {
            board.position(data.fen)
        },
        'game_number' : function(data) {
            $('#game_number').html("Game # " + data.game_number);
        },
        'initial_time_mins': function(data) {
            $('#initial_time_mins').html(data.initial_time_mins+ '/');
        },
        'white_time_remain': function(data) {
            clearInterval(counter_w);
            if(data.turn_color == "W") {
                remain_w = data.white_time_remain;
                counter_w = setInterval(timer_w, 4);
            }
        },
        'black_time_remain': function(data) {
            clearInterval(counter_b);
            if(data.turn_color == "B") {
                remain_b = data.black_time_remain;
                counter_b = setInterval(timer_b, 4);
            }
        }
    };

    ///////////////////////////////

    var enable_send = function() {
        $('button#send').removeClass('btn-danger');
        $('button#send').addClass('btn-success');
    };
    var disable_send = function() {
        $('button#send').removeClass('btn-success');
        $('button#send').addClass('btn-danger');
    };


    ///////////////////////////////


    var socket = io.connect('http://' + document.domain + ':' + location.port);
    socket.on('connect', function(m) { // socket is connected
        socket.emit('connected',{});
    });
    socket.on('disconnect', function(m) { // socket is connected
        disable_send();
    });
    socket.on('message', function(m) { // message from socket
        $('div#fics pre').prepend(m.data).fadeIn();
    });
    socket.on('exception', function(m) { // exception from socket
        alert('exception, disconnecting: ' + m.data);
        socket.disconnect();
    });
    socket.on('ficsup', function(m) { // logged in to fics
        $(':disabled').each(function(i,el) {
            $(el).attr('disabled', false);
        });
        enable_send();
    });
    socket.on('board-state', function(m) { // update html state
        console.log(m.data);
        $.each(m.data, function(k, v) {
            if( k in override ) {
                // execute custom update logic
                override[k](m.data);
            }
            else { // default logic: update #id (if it exists)
                var target_id = "#" + k;
                if ( $(target_id).length > 0 ) {
                    $(target_id).html( v );
                }
            }
        });
    });

    ///////////////////////////////

    $('form').submit(function(e){
        e.preventDefault();
        socket.emit('command', {data: $(this).find('input').val()});
    });

});

