from urllib2 import urlopen
from urllib import urlencode


if __name__ == "__main__":
    admob_post = {}
    # specific site ID for each app
    admob_post["s"] = "a1502297e61c9b4"
    admob_post["u"] = "Mozilla/5.0 (Windows NT 6.2; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) " + \
                      "Chrome/32.0.1667.0 Safari/537.36"
    admob_post["e"] = "UTF-8"
    admob_post["v"] = "20140219-PYTHON"
    admob_post["k"] = "keywords, for, ad, selection"
    # if not in test mode, don't pass m
    admob_post["m"] = "test"

    admob_data = urlencode(admob_post)
    print "data", admob_data
    admob_file = urlopen("http://r.admob.com/ad_source.php", admob_data)
    admob_contents = admob_file.read()
    print "contents", admob_contents

