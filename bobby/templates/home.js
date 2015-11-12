$(function() {

    var board = ChessBoard('board', {
        'position'      : 'start',
        'pieceTheme'    : '/static/img/chesspieces/wikipedia/{piece}.png',
		'draggable' 	: false
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
			console.log('orientation');
			console.log(data.orientation);
            board.orientation(data.orientation);
			console.log(board.orientation());
        },
        'fen' : function(data) {
            var animated = false;
            board.position(data.fen, animated);
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
        },
		'my_relation' : function(data) {
            console.log(data);
			var ISOLATED            = -3;
            var OBSERVING_EXAM      = -2;
            var EXAMINER            = 2;
            var PLAYING_THEIR_MOVE  = -1;
            var PLAYING_MY_MOVE     = 1;
            var OBSERVING           = 0;
            console.log(data.my_relation);
            switch(parseInt(data.my_relation))
            {
                case PLAYING_MY_MOVE:
                    board.draggable = true;
                    console.log(board);
                default:
                    board.draggable = false;
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
        socket.disconnect();
    });
    socket.on('message', function(m) { // message from socket
        $('div#fics pre').append(m.data);
        console.log($('div#fics pre').prop('scrollHeight'));
        $('div#fics').animate({scrollTop: $('div#fics').prop('scrollHeight')}, 500);
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
    socket.on('game-state', function(m) {
        var state   = Object.keys(m.data)[0];
        var message = m.data[state];
        $('div#game-state').html(message);
        switch(state) {
            case 'start': break;
            default:        // draw, abort, resign, etc...
                clearInterval(counter_w);
                clearInterval(counter_b);
				$('div#left game-info').contents().filter(function(){
					return this.nodeType === 3;
				}).remove();
        }
    });
    socket.on('board-state', function(m) { // update html state
        if(typeof m.data === 'object') {
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
        } else {
            console.warn('messsage data is not an object');
            console.warn(m.data);
        }
    });

    ///////////////////////////////

    $('form#cli').submit(function(e){
        e.preventDefault();
        socket.emit('command', {data: $(this).find('input').val()});
        $(this).find('input').val('');
    });

    $('form#seek').submit(function(e){
        e.preventDefault();
        var time = $('input#time').val();
        var increment = $('input#increment').val();
        socket.emit('command', {data: 'seek ' + time + ' ' + increment});
    });


    $('button#flip').click(function(){
        board.flip();
    });

    $('button#gg').click(function(){
        socket.emit('command', {data: 'say gg'});
    });

    $('button#bg').click(function(){
        socket.emit('command', {data: 'say bg'});
    });

    $('button#resign').click(function(){
        socket.emit('command', {data: 'resign'});
    });

    $('button#draw').click(function(){
        socket.emit('command', {data: 'draw'});
    });

    $('button#abort').click(function(){
        socket.emit('command', {data: 'abort'});
    });

});

