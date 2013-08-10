import urllib2
import StringIO
import gzip
import lxml.etree as ElementTree
import time
import datetime
import re
import sys
import csv


def trimTimestamp(ts):
    if ts:
        return re.sub('[Z]', ' ', ts)
    else:
        return ts


def recode(s):
    if s:
        return s.encode('utf8')
    else:
        return s


def parseChangesets(source, cs_out, tag_out):
    parent_obj = None
    sequence = 0
    for event, elem in ElementTree.iterparse(source, events=('start', 'end')):
        if event == 'start':
            if elem.tag == 'changeset':
                cs_out.writerow({
                    "id": elem.attrib['id'],
                    "created_at": trimTimestamp(elem.attrib['created_at']),
                    "closed_at": trimTimestamp(elem.attrib.get('closed_at')),
                    "userid": elem.get('uid'),
                    "username": recode(elem.get('user')),
                    "bottom": elem.get('min_lat'),
                    "top": elem.get('max_lat'),
                    "left": elem.get('min_lon'),
                    "right": elem.get('max_lon')
                })
                parent_obj = elem.attrib['id']
            elif elem.tag == 'tag':
                tag_out.writerow({
                    "changeset_id": parent_obj,
                    "sequence": sequence,
                    "key": recode(elem.attrib['k']),
                    "value": recode(elem.attrib['v'])
                })
                sequence += 1
        elif event == 'end':
            if elem.tag == 'changeset':
                parent_obj = None
                sequence = 0

        elem.clear()


def minutelyUpdateRun(state, cur):
    # Grab the next sequence number and build a URL out of it
    sqnStr = state['sequenceNumber'].zfill(9)
    url = "http://planet.openstreetmap.org/replication/minute/%s/%s/%s.osc.gz" % (sqnStr[0:3], sqnStr[3:6], sqnStr[6:9])

    print "Downloading change file (%s)." % (url)
    content = urllib2.urlopen(url)
    content = StringIO.StringIO(content.read())
    gzipper = gzip.GzipFile(fileobj=content)

    print "Parsing change file."
    return parseChangesets(gzipper, cur)


def readState(state_file):
    state = {}

    for line in state_file:
        if line[0] == '#':
            continue
        (k, v) = line.split('=')
        state[k] = v.strip().replace("\\:", ":")

    return state


def fetchNextState(currentState):
    # Download the next state file
    nextSqn = int(currentState['sequenceNumber']) + 1
    sqnStr = str(nextSqn).zfill(9)
    url = "http://planet.openstreetmap.org/replication/minute/%s/%s/%s.state.txt" % (sqnStr[0:3], sqnStr[3:6], sqnStr[6:9])
    try:
        u = urllib2.urlopen(url)
        statefile = readState(u)
        statefile['sequenceNumber'] = nextSqn

        sf_out = open('state.txt', 'w')
        for (k, v) in statefile.iteritems():
            sf_out.write("%s=%s\n" % (k, v))
        sf_out.close()
    except Exception, e:
        print e
        return False

    return True


if __name__ == "__main__":
    #con = mdb.connect('osmhistory.cb95w14zt4sv.us-east-1.rds.amazonaws.com', 'osmuser', 'osmpassword', 'osmarchive', charset='utf8')
    #con = mdb.connect('db.mapki.com', 'osmarchive', 'osmarchivepassword', 'osmarchive', charset='utf8')
    #cur = con.cursor()

    cs_fields = ["id", "created_at", "closed_at", "userid", "username", "top", "left", "bottom", "right"]
    changeset_out = csv.DictWriter(open('changesets.csv', 'w'), cs_fields)
    changeset_out.writeheader()
    cs_tag_fields = ["changeset_id", "sequence", "key", "value"]
    changeset_tag_out = csv.DictWriter(open('changeset_tags.csv', 'w'), cs_tag_fields)
    changeset_tag_out.writeheader()

    parseChangesets(open(sys.argv[1]), changeset_out, changeset_tag_out)

    sys.exit(0)

    while True:
        state = readState(open('state.txt', 'r'))

        start = time.time()
        minutelyUpdateRun(state, cur)

        con.commit()

        elapsed = time.time() - start
        print "Inserted in %2.1f seconds." % (elapsed)

        stateTs = datetime.datetime.strptime(state['timestamp'], "%Y-%m-%dT%H:%M:%SZ")
        nextTs = stateTs + datetime.timedelta(minutes=1)

        if datetime.datetime.utcnow() < nextTs:
            timeToSleep = (nextTs - datetime.datetime.utcnow()).seconds + 13.0
        else:
            timeToSleep = 0.0
        print "Waiting %2.1f seconds for the next state.txt." % (timeToSleep)
        time.sleep(timeToSleep)

        result = fetchNextState(state)

        if not result:
            print "Couldn't continue. Sleeping %2.1f more seconds." % (15.0)
            time.sleep(15.0)
