function t(n) {
    for (var o = "", e = 0; e < n.length; e++) {
        var t = n[e].toString(16);
        o += t = 1 === t.length ? "0" + t : t
    }
    return o
}

function e(n) {
    function o(n, o) {
        return n << o | n >>> 32 - o
    }

    var e = [1518500249, 1859775393, 2400959708, 3395469782]
        , t = [1732584193, 4023233417, 2562383102, 271733878, 3285377520];
    if ("string" == typeof n) {
        var i = unescape(encodeURIComponent(n));
        n = new Array(i.length);
        for (c = 0; c < i.length; c++)
            n[c] = i.charCodeAt(c)
    }
    n.push(128);
    for (var r = n.length / 4 + 2, a = Math.ceil(r / 16), d = new Array(a), c = 0; c < a; c++) {
        d[c] = new Array(16);
        for (var s = 0; s < 16; s++)
            d[c][s] = n[64 * c + 4 * s] << 24 | n[64 * c + 4 * s + 1] << 16 | n[64 * c + 4 * s + 2] << 8 | n[64 * c + 4 * s + 3]
    }
    d[a - 1][14] = 8 * (n.length - 1) / Math.pow(2, 32),
        d[a - 1][14] = Math.floor(d[a - 1][14]),
        d[a - 1][15] = 8 * (n.length - 1) & 4294967295;
    for (c = 0; c < a; c++) {
        for (var p = new Array(80), m = 0; m < 16; m++)
            p[m] = d[c][m];
        for (m = 16; m < 80; m++)
            p[m] = o(p[m - 3] ^ p[m - 8] ^ p[m - 14] ^ p[m - 16], 1);
        for (var w = t[0], f = t[1], g = t[2], u = t[3], _ = t[4], m = 0; m < 80; m++) {
            var h = Math.floor(m / 20)
                , l = o(w, 5) + function (n, o, e, t) {
                switch (n) {
                    case 0:
                        return o & e ^ ~o & t;
                    case 1:
                        return o ^ e ^ t;
                    case 2:
                        return o & e ^ o & t ^ e & t;
                    case 3:
                        return o ^ e ^ t
                }
            }(h, f, g, u) + _ + e[h] + p[m] >>> 0;
            _ = u,
                u = g,
                g = o(f, 30) >>> 0,
                f = w,
                w = l
        }
        t[0] = t[0] + w >>> 0,
            t[1] = t[1] + f >>> 0,
            t[2] = t[2] + g >>> 0,
            t[3] = t[3] + u >>> 0,
            t[4] = t[4] + _ >>> 0
    }
    return [t[0] >> 24 & 255, t[0] >> 16 & 255, t[0] >> 8 & 255, 255 & t[0], t[1] >> 24 & 255, t[1] >> 16 & 255, t[1] >> 8 & 255, 255 & t[1], t[2] >> 24 & 255, t[2] >> 16 & 255, t[2] >> 8 & 255, 255 & t[2], t[3] >> 24 & 255, t[3] >> 16 & 255, t[3] >> 8 & 255, 255 & t[3], t[4] >> 24 & 255, t[4] >> 16 & 255, t[4] >> 8 & 255, 255 & t[4]]
}

function n(n, a, d, c) {
    var r = {bw: 1930, bh: 919}
        // , a = location.href
        // , d = navigator.userAgent
        // , c = document.cookie
        , o = undefined
        , s = 1e9 * Math.random() << 0
        , p = (new Date).getTime()
        , m = t(e([r.bw + "" + r.bh, a, d, c, s, p, n].join("-"))).slice(20);
    return o ? m : m + "-" + p.toString(16)
}


function createHash(e) {
    if (null === e)
        return null;
    var t, n, r, a, i, o, s, c, l, u, d, h = function (e, t) {
        return e << t | e >>> 32 - t
    }, f = function (e, t) {
        var n, r, a, i, o;
        return a = 2147483648 & e,
            i = 2147483648 & t,
            o = (1073741823 & e) + (1073741823 & t),
            (n = 1073741824 & e) & (r = 1073741824 & t) ? 2147483648 ^ o ^ a ^ i : n | r ? 1073741824 & o ? 3221225472 ^ o ^ a ^ i : 1073741824 ^ o ^ a ^ i : o ^ a ^ i
    }, p = function (e, t, n, r, a, i, o) {
        return e = f(e, f(f(function (e, t, n) {
            return e & t | ~e & n
        }(t, n, r), a), o)),
            f(h(e, i), t)
    }, m = function (e, t, n, r, a, i, o) {
        return e = f(e, f(f(function (e, t, n) {
            return e & n | t & ~n
        }(t, n, r), a), o)),
            f(h(e, i), t)
    }, g = function (e, t, n, r, a, i, o) {
        return e = f(e, f(f(function (e, t, n) {
            return e ^ t ^ n
        }(t, n, r), a), o)),
            f(h(e, i), t)
    }, v = function (e, t, n, r, a, i, o) {
        return e = f(e, f(f(function (e, t, n) {
            return t ^ (e | ~n)
        }(t, n, r), a), o)),
            f(h(e, i), t)
    }, y = function (e) {
        var t, n = "", r = "";
        for (t = 0; t <= 3; t++)
            n += (r = "0" + (e >>> 8 * t & 255).toString(16)).substr(r.length - 2, 2);
        return n
    };
    for (c = 1732584193,
             l = 4023233417,
             u = 2562383102,
             d = 271733878,
             t = (n = function (e) {
                 for (var t, n = e.length, r = n + 8, a = 16 * ((r - r % 64) / 64 + 1), i = new Array(a - 1), o = 0, s = 0; s < n;)
                     o = s % 4 * 8,
                         i[t = (s - s % 4) / 4] = i[t] | e.charCodeAt(s) << o,
                         s++;
                 return o = s % 4 * 8,
                     i[t = (s - s % 4) / 4] = i[t] | 128 << o,
                     i[a - 2] = n << 3,
                     i[a - 1] = n >>> 29,
                     i
             }(e)).length,
             r = 0; r < t; r += 16)
        a = c,
            i = l,
            o = u,
            s = d,
            c = p(c, l, u, d, n[r + 0], 7, 3614090360),
            d = p(d, c, l, u, n[r + 1], 12, 3905402710),
            u = p(u, d, c, l, n[r + 2], 17, 606105819),
            l = p(l, u, d, c, n[r + 3], 22, 3250441966),
            c = p(c, l, u, d, n[r + 4], 7, 4118548399),
            d = p(d, c, l, u, n[r + 5], 12, 1200080426),
            u = p(u, d, c, l, n[r + 6], 17, 2821735955),
            l = p(l, u, d, c, n[r + 7], 22, 4249261313),
            c = p(c, l, u, d, n[r + 8], 7, 1770035416),
            d = p(d, c, l, u, n[r + 9], 12, 2336552879),
            u = p(u, d, c, l, n[r + 10], 17, 4294925233),
            l = p(l, u, d, c, n[r + 11], 22, 2304563134),
            c = p(c, l, u, d, n[r + 12], 7, 1804603682),
            d = p(d, c, l, u, n[r + 13], 12, 4254626195),
            u = p(u, d, c, l, n[r + 14], 17, 2792965006),
            c = m(c, l = p(l, u, d, c, n[r + 15], 22, 1236535329), u, d, n[r + 1], 5, 4129170786),
            d = m(d, c, l, u, n[r + 6], 9, 3225465664),
            u = m(u, d, c, l, n[r + 11], 14, 643717713),
            l = m(l, u, d, c, n[r + 0], 20, 3921069994),
            c = m(c, l, u, d, n[r + 5], 5, 3593408605),
            d = m(d, c, l, u, n[r + 10], 9, 38016083),
            u = m(u, d, c, l, n[r + 15], 14, 3634488961),
            l = m(l, u, d, c, n[r + 4], 20, 3889429448),
            c = m(c, l, u, d, n[r + 9], 5, 568446438),
            d = m(d, c, l, u, n[r + 14], 9, 3275163606),
            u = m(u, d, c, l, n[r + 3], 14, 4107603335),
            l = m(l, u, d, c, n[r + 8], 20, 1163531501),
            c = m(c, l, u, d, n[r + 13], 5, 2850285829),
            d = m(d, c, l, u, n[r + 2], 9, 4243563512),
            u = m(u, d, c, l, n[r + 7], 14, 1735328473),
            c = g(c, l = m(l, u, d, c, n[r + 12], 20, 2368359562), u, d, n[r + 5], 4, 4294588738),
            d = g(d, c, l, u, n[r + 8], 11, 2272392833),
            u = g(u, d, c, l, n[r + 11], 16, 1839030562),
            l = g(l, u, d, c, n[r + 14], 23, 4259657740),
            c = g(c, l, u, d, n[r + 1], 4, 2763975236),
            d = g(d, c, l, u, n[r + 4], 11, 1272893353),
            u = g(u, d, c, l, n[r + 7], 16, 4139469664),
            l = g(l, u, d, c, n[r + 10], 23, 3200236656),
            c = g(c, l, u, d, n[r + 13], 4, 681279174),
            d = g(d, c, l, u, n[r + 0], 11, 3936430074),
            u = g(u, d, c, l, n[r + 3], 16, 3572445317),
            l = g(l, u, d, c, n[r + 6], 23, 76029189),
            c = g(c, l, u, d, n[r + 9], 4, 3654602809),
            d = g(d, c, l, u, n[r + 12], 11, 3873151461),
            u = g(u, d, c, l, n[r + 15], 16, 530742520),
            c = v(c, l = g(l, u, d, c, n[r + 2], 23, 3299628645), u, d, n[r + 0], 6, 4096336452),
            d = v(d, c, l, u, n[r + 7], 10, 1126891415),
            u = v(u, d, c, l, n[r + 14], 15, 2878612391),
            l = v(l, u, d, c, n[r + 5], 21, 4237533241),
            c = v(c, l, u, d, n[r + 12], 6, 1700485571),
            d = v(d, c, l, u, n[r + 3], 10, 2399980690),
            u = v(u, d, c, l, n[r + 10], 15, 4293915773),
            l = v(l, u, d, c, n[r + 1], 21, 2240044497),
            c = v(c, l, u, d, n[r + 8], 6, 1873313359),
            d = v(d, c, l, u, n[r + 15], 10, 4264355552),
            u = v(u, d, c, l, n[r + 6], 15, 2734768916),
            l = v(l, u, d, c, n[r + 13], 21, 1309151649),
            c = v(c, l, u, d, n[r + 4], 6, 4149444226),
            d = v(d, c, l, u, n[r + 11], 10, 3174756917),
            u = v(u, d, c, l, n[r + 2], 15, 718787259),
            l = v(l, u, d, c, n[r + 9], 21, 3951481745),
            c = f(c, a),
            l = f(l, i),
            u = f(u, o),
            d = f(d, s);
    return (y(c) + y(l) + y(u) + y(d)).toLowerCase()
}






