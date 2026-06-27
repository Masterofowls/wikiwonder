vcl 4.1;

# WikiWonder — Varnish in front of Django (nginx terminates TLS upstream)
# https://www.varnish.org/

backend django {
    .host = "web";
    .port = "8000";
    .connect_timeout = 5s;
    .first_byte_timeout = 120s;
    .between_bytes_timeout = 120s;
}

sub vcl_recv {
    # Trust X-Forwarded-* from nginx
    if (req.http.X-Forwarded-Proto) {
        set req.http.X-Forwarded-Proto = req.http.X-Forwarded-Proto;
    }

    # Only cache GET/HEAD
    if (req.method != "GET" && req.method != "HEAD") {
        return (pass);
    }

    # Never cache admin, auth, API mutations, health, or MCP
    if (req.url ~ "^/(admin|accounts|api/|health|markdownx|rosetta|django-check-seo|feeds/)") {
        return (pass);
    }

    # Logged-in users (session cookie) always hit origin
    if (req.http.Cookie ~ "(sessionid|csrftoken)") {
        return (pass);
    }

    # POST-like query strings
    if (req.url ~ "(\?|&)(csrfmiddlewaretoken|_)=") {
        return (pass);
    }

    return (hash);
}

sub vcl_backend_response {
    # Respect origin Cache-Control; default TTL for cacheable 200s without header
    if (beresp.status == 200 && !beresp.http.Cache-Control) {
        set beresp.ttl = 120s;
        set beresp.http.Cache-Control = "public, max-age=120";
    }

    # Do not cache errors or redirects
    if (beresp.status >= 400 || beresp.status == 301 || beresp.status == 302) {
        set beresp.ttl = 0s;
        set beresp.uncacheable = true;
        return (deliver);
    }

    # Strip Set-Cookie on cacheable anonymous pages
    if (beresp.http.Set-Cookie) {
        set beresp.uncacheable = true;
        return (deliver);
    }

    return (deliver);
}

sub vcl_deliver {
    if (obj.hits > 0) {
        set resp.http.X-Cache = "HIT";
    } else {
        set resp.http.X-Cache = "MISS";
    }
    set resp.http.X-Cache-Varnish = "WikiWonder";
    unset resp.http.Via;
}
