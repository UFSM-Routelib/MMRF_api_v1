from flask import Blueprint, request, jsonify
from . import db
from .models import Poste, Edge
from math import sin, cos, sqrt, atan2, radians
import time

funcs = Blueprint("funcs", __name__)


@funcs.route("add-node", methods=['POST'])
def addVertex():

    content_type = request.headers.get('Content-Type')

    if (content_type == 'application/json'):

        body = request.json

        fplaq = body['id']
        flng = body['lng']
        flat = body['lat']

        real_first = Poste.query.filter_by(plaq=fplaq).first()

        if real_first is None:

            n1 = Poste(plaq=fplaq, cordx=flng, cordy=flat)

        db.session.add(n1)
        db.session.commit()

        return body
    else:
        return 'Content-Type not supported!', 400


@funcs.route("/add-edge", methods=['POST'])
def addEdge():

    content_type = request.headers.get('Content-Type')

    if (content_type == 'application/json'):

        body = request.json

        fplaq = body['node1']

        n1 = Poste.query.filter_by(plaq=fplaq).first()

        if n1 is None:
            return 'Invalid font', 400

        nplaq = body['node2']

        n2 = Poste.query.filter_by(plaq=nplaq).first()

        if n2 is None:
            return 'invalid end', 400

        dist = 1  # REMOVE DEBUG TEST

        edge = Edge(node1 = n1.plaq, node2=n2.plaq, id=(str(n1.plaq) + str(n2.plaq)), distance=int(dist))
        edge2 = Edge(node1 = n2.plaq, node2=n1.plaq, id=(str(n2.plaq) + str(n1.plaq)), distance=int(dist))

        db.session.add(edge)
        db.session.add(edge2)
        db.session.commit()

        return body
    else:
        return 'Content-Type not supported!', 400


@funcs.route("/show-poste", methods=['GET'])
def showPoste():

    postes = Poste.query.all()

    for p in postes:
        print(f'{p.plaq} {p.cordx} {p.cordy}')

    return jsonify(postes)


@funcs.route("/show-graph", methods=['GET'])
def showGraph():

    postes = Poste.query.all()
    nodes = []

    for p in postes:
        cons = Edge.query.filter_by(node1=p.plaq).all()
        node = (p.plaq, [(con.id, con.distance) for con in cons])
        nodes.append(node)

    return jsonify(nodes)


@funcs.route("/all-paths-limited/", methods=["POST"])
def allPathsLimited():

    start = time.time()

    content_type = request.headers.get('Content-Type')

    if (content_type == 'application/json'):

        body = request.json

        plaq = body['plaq']

        a = (body['lat1'], body['lng1'])  # a and b will be the square_cors, the delimiters
        b = (body['lat2'], body['lng2'])

        print(a)
        print(b)

        def inbetweeen(p, x, y):
            if p >= x and p <= y:
                return True
            return False

        def findAllRealPaths(start, end, limit, path=[], paths=[], cost=0, ):
            path = path + [(start.cordx, start.cordy)]

            if start.plaq == end.plaq:
                pair = [path, cost]
                paths.append(pair)

            if cost > limit:
                return None

            for con in Edge.query.filter_by(node1=start.plaq):

                node = Poste.query.filter_by(plaq=con.node2).first()

                if inbetweeen(node.cordx, b[0], a[0]) and inbetweeen(node.cordy, a[1], b[1]):

                    if (node.cordx, node.cordy) not in path:
                        findAllRealPaths(start=node, end=end, limit=limit, path=path, paths=paths, cost=(cost + con.distance))

            return paths

        def visitAllNeighboursLimited(start, limit):

            paths = []

            for node in Poste.query.all():

                paths_node = findAllRealPaths(start, node, limit)

                for path in paths_node:
                    if path not in paths:
                        paths.append(path)

            return paths

        n1 = int(plaq)

        p1 = Poste.query.filter_by(plaq=n1).first()

        x = visitAllNeighboursLimited(p1, 100)
        print(time.time() - start)
        print(x)
        return jsonify(x)


@funcs.route("/closest-poste/", methods=["POST"])
def closest_poste():

    print("cp ran")

    content_type = request.headers.get('Content-Type')

    if (content_type == 'application/json'):

        body = request.json

        lat = body['lat']
        lng = body['lng']

        reference = (float(lat), float(lng))

        def get_distance(point1, point2):
            R = 6370
            lat1 = radians(point1[0])
            lon1 = radians(point1[1])
            lat2 = radians(point2[0])
            lon2 = radians(point2[1])

            dlon = lon2 - lon1
            dlat = lat2 - lat1

            a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
            c = 2 * atan2(sqrt(a), sqrt(1-a))
            distance = R * c
            return distance

        closest = None  # o poste mais perto
        shortest = 0    # distancia do poste mais perto

        for poste in Poste.query.all():

            distance = get_distance(reference, (poste.cordx, poste.cordy))

            if closest is None or distance < shortest:

                closest = poste
                shortest = distance

        if closest is not None:
            pair = [closest.plaq, (closest.cordx, closest.cordy), shortest]

            print(pair)

            return jsonify(pair), 200
        else:
            return "invalid", 400
    return "invalid", 400
