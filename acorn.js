var data = '';
process.stdin.resume();
process.stdin.setEncoding('utf8');
process.stdin.on('data', function(chunk) {data += chunk;});
process.stdin.on('end', function() {
    try {
        process.stdout.write(JSON.stringify(require('acorn').parse(data)));
    } catch(e) {
        process.stdout.write(JSON.stringify({
            'error': true,
            'error_message': e.toString(),
            'line_number': e.loc.line
        }));
    }
    process.exit(0);
});
