import MySQLdb as mdb
import urllib2
import StringIO
import gzip
import lxml.etree as ElementTree
import time
import datetime
import re


def parseOsm(source, cur):
    nodes = []
    node_tags = []
    ways = []
    way_tags = []
    way_nodes = []
    relations = []
    relation_tags = []
    relation_members = []
    parent_obj = None
    sequence = 0
    for event, elem in ElementTree.iterparse(source, events=('start', 'end')):
        if event == 'start':
            if elem.tag == 'node':
                nodes.append({
                    "id": elem.attrib['id'],
                    "version": elem.attrib['version'],
                    "changeset": elem.attrib['changeset'],
                    "userid": elem.attrib['uid'],
                    "username": elem.get('user'),
                    "timestamp": re.sub('[TZ]', ' ', elem.attrib['timestamp']),
                    "lat": elem.attrib['lat'],
                    "lon": elem.attrib['lon']
                })
                parent_obj = ('n', elem.attrib['id'], elem.attrib['version'])
            elif elem.tag == 'way':
                ways.append({
                    "id": elem.attrib['id'],
                    "version": elem.attrib['version'],
                    "changeset": elem.attrib['changeset'],
                    "userid": elem.attrib['uid'],
                    "username": elem.get('user'),
                    "timestamp": re.sub('[TZ]', ' ', elem.attrib['timestamp'])
                })
                parent_obj = ('w', elem.attrib['id'], elem.attrib['version'])
            elif elem.tag == 'relation':
                relations.append({
                    "id": elem.attrib['id'],
                    "version": elem.attrib['version'],
                    "changeset": elem.attrib['changeset'],
                    "userid": elem.attrib['uid'],
                    "username": elem.get('user'),
                    "timestamp": re.sub('[TZ]', ' ', elem.attrib['timestamp'])
                })
                parent_obj = ('r', elem.attrib['id'], elem.attrib['version'])
            elif elem.tag == 'tag':
                obj_type = parent_obj[0]
                if obj_type == 'n':
                    node_tags.append({
                        "node_id": parent_obj[1],
                        "node_version": parent_obj[2],
                        "sequence": sequence,
                        "key": elem.attrib['k'],
                        "value": elem.attrib['v']
                    })
                elif obj_type == 'w':
                    way_tags.append({
                        "way_id": parent_obj[1],
                        "way_version": parent_obj[2],
                        "sequence": sequence,
                        "key": elem.attrib['k'],
                        "value": elem.attrib['v']
                    })
                elif obj_type == 'r':
                    relation_tags.append({
                        "relation_id": parent_obj[1],
                        "relation_version": parent_obj[2],
                        "sequence": sequence,
                        "key": elem.attrib['k'],
                        "value": elem.attrib['v']
                    })
                sequence += 1
            elif elem.tag == 'nd':
                way_nodes.append({
                    "way_id": parent_obj[1],
                    "way_version": parent_obj[2],
                    "node_order": sequence,
                    "node_id": elem.attrib['ref']
                })
                sequence += 1
            elif elem.tag == 'member':
                relation_members.append({
                    "relation_id": parent_obj[1],
                    "relation_version": parent_obj[2],
                    "member_role": elem.attrib['role'],
                    "member_type": elem.attrib['type'],
                    "member_id": elem.attrib['ref'],
                    "member_order": sequence
                })
                sequence += 1
        elif event == 'end':
            if elem.tag in ('node', 'way', 'relation'):
                parent_obj = None
                sequence = 0

            elif elem.tag == 'osmChange':
                if nodes:
                    node_rows = cur.executemany("INSERT INTO `osm_nodes` (`id`, `version`, `changeset`, `userid`, `username`, `timestamp`, `lat`, `lon`) VALUES (%(id)s, %(version)s, %(changeset)s, %(userid)s, %(username)s, %(timestamp)s, %(lat)s, %(lon)s)", nodes)
                    print "Inserted %s node rows." % node_rows
                if node_tags:
                    node_tag_rows = cur.executemany("INSERT INTO `osm_node_tags` (`node_id`, `node_version`, `sequence`, `key`, `value`) VALUES (%(node_id)s, %(node_version)s, %(sequence)s, %(key)s, %(value)s)", node_tags)
                    print "Inserted %s node tag rows." % node_tag_rows
                nodes = []
                node_tags = []

                if ways:
                    way_rows = cur.executemany("INSERT INTO `osm_ways` (`id`, `version`, `changeset`, `userid`, `username`, `timestamp`) VALUES (%(id)s, %(version)s, %(changeset)s, %(userid)s, %(username)s, %(timestamp)s)", ways)
                    print "Inserted %s way rows." % way_rows
                if way_tags:
                    way_tag_rows = cur.executemany("INSERT INTO `osm_way_tags` (`way_id`, `way_version`, `sequence`, `key`, `value`) VALUES (%(way_id)s, %(way_version)s, %(sequence)s, %(key)s, %(value)s)", way_tags)
                    print "Inserted %s way tag rows." % way_tag_rows
                if way_nodes:
                    way_node_rows = cur.executemany("INSERT INTO `osm_way_nodes` (`way_id`, `way_version`, `node_order`, `node_id`) VALUES (%(way_id)s, %(way_version)s, %(node_order)s, %(node_id)s)", way_nodes)
                    print "Inserted %s way node rows." % way_node_rows
                ways = []
                way_tags = []
                way_nodes = []

                if relations:
                    relation_rows = cur.executemany("INSERT INTO `osm_relations` (`id`, `version`, `changeset`, `userid`, `username`, `timestamp`) VALUES (%(id)s, %(version)s, %(changeset)s, %(userid)s, %(username)s, %(timestamp)s)", relations)
                    print "Inserted %s relation rows." % relation_rows
                if relation_tags:
                    relation_tag_rows = cur.executemany("INSERT INTO `osm_relation_tags` (`relation_id`, `relation_version`, `sequence`, `key`, `value`) VALUES (%(relation_id)s, %(relation_version)s, %(sequence)s, %(key)s, %(value)s)", relation_tags)
                    print "Inserted %s relation tag rows." % relation_tag_rows
                if relation_members:
                    relation_member_rows = cur.executemany("INSERT INTO `osm_relation_members` (`relation_id`, `relation_version`, `member_role`, `member_type`, `member_id`, `member_order`) VALUES (%(relation_id)s, %(relation_version)s, %(member_role)s, %(member_type)s, %(member_id)s, %(member_order)s)", relation_members)
                    print "Inserted %s relation member rows." % relation_member_rows
                relations = []
                relation_tags = []
                relation_members = []
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
    return parseOsm(gzipper, cur)


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
    con = mdb.connect('osmhistory.cb95w14zt4sv.us-east-1.rds.amazonaws.com', 'osmuser', 'osmpassword', 'osmarchive', charset='utf8')
    #con = mdb.connect('db.mapki.com', 'osmarchive', 'osmarchivepassword', 'osmarchive', charset='utf8')
    cur = con.cursor()

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
