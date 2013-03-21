def process_request(request):
    visitor_info = request.session.get('visitor_info')
    result = {}
    if visitor_info:
        result['visitor_info'] = visitor_info
    return result