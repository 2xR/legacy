import os, sys

exts = set(["py", "lua", "c", "cpp"])
count_empty_line = False
here = os.path.abspath(os.path.dirname(sys.argv[1]))

def read_line_count(fname):
    count = 0
    with open(fname, "r") as f:
        for line in f:
            if count_empty_line or len(line.strip()) > 0:
                count += 1
    return count
    
def main():
    line_count = 0
    file_count = 0
    for base, _, fnames in os.walk(here):
        print base
        for fname in fnames:
            # Check the sub directorys            
            if fname.find('.') < 0:
                continue
            ext = fname.rsplit(".", 1)[1].lower()
            if ext in exts:
                file_count += 1
                c = read_line_count(os.path.join(base, fname))
                print "%30s : %d" % (fname, c)
                line_count += c
            
    print 'Total file count : %d' % file_count
    print 'Total line count : %d' % line_count
    
if __name__ == '__main__':
    main()
    
    
