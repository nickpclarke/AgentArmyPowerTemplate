"""RDF (Turtle / JSON-LD / N-Triples) → forge IR.

Accepts a deliberately constrained OWL-shaped vocabulary — NOT arbitrary OWL.
The forge contract is "any tool can produce this; any RDF parser can read it";
the constraint is what we accept on read.

ACCEPTED VOCABULARY
-------------------

Prefixes:
    forge: http://agentarmy.dev/forge#
    owl:   http://www.w3.org/2002/07/owl#
    rdf:   http://www.w3.org/1999/02/22-rdf-syntax-ns#
    rdfs:  http://www.w3.org/2000/01/rdf-schema#
    xsd:   http://www.w3.org/2001/XMLSchema#

Model header (one triple in the graph):
    [ a forge:Model ;
      forge:version "1.0.0" ;
      forge:namespace "AgentArmy.MiddleCore.Contracts" ] .

ObjectType declarations — one OWL class per type:
    ex:Document a owl:Class ;
        forge:fieldOrder ( "id" "title" "body" "createdAt" ) ;
        forge:relationOrder ( "author" ) .

Fields — OWL datatype properties with rdfs:domain pointing at the OT:
    ex:title a owl:DatatypeProperty ;
        rdfs:domain ex:Document ;
        rdfs:range xsd:string ;
        forge:optional false .

Relations — OWL object properties with rdfs:domain + rdfs:range:
    ex:author a owl:ObjectProperty ;
        rdfs:domain ex:Document ;
        rdfs:range ex:User ;
        forge:cardinality "one" ;
        forge:inverse "documents" .

XSD scalar → forge primitive map:
    xsd:string     -> string
    xsd:integer    -> int
    xsd:int        -> int
    xsd:long       -> long
    xsd:float      -> float
    xsd:double     -> float
    xsd:decimal    -> float
    xsd:boolean    -> bool
    xsd:dateTime   -> datetime
    xsd:date       -> datetime
    forge:uuid     -> uuid
    forge:json     -> json

Anything outside this vocabulary is **silently ignored**. The IR is the
contract — forge is not an OWL reasoner.

If `forge:fieldOrder` / `forge:relationOrder` lists are absent, fields and
relations are sorted lexicographically. This loses author-intended ordering
but makes the IR deterministic, which is what the byte-identical doctor
check depends on.

Format detection is by file extension on Source adapters (`.ttl`, `.jsonld`,
`.nt`) — this module parses any of them via rdflib.
"""
from __future__ import annotations

import io
from typing import Optional

from rdflib import Graph, Literal, URIRef
from rdflib.collection import Collection
from rdflib.namespace import OWL, RDF, RDFS, XSD, Namespace

from ..ir import Field, Model, ObjectType, Relation

FORGE = Namespace("http://agentarmy.dev/forge#")

# XSD datatype URI -> forge primitive name.
_XSD_TO_FORGE: dict[URIRef, str] = {
    XSD.string: "string",
    XSD.integer: "int",
    XSD.int: "int",
    XSD.long: "long",
    XSD.float: "float",
    XSD.double: "float",
    XSD.decimal: "float",
    XSD.boolean: "bool",
    XSD.dateTime: "datetime",
    XSD.date: "datetime",
    FORGE.uuid: "uuid",
    FORGE.json: "json",
}


def parse(source: str | bytes, source_uri: Optional[str] = None) -> Model:
    """Load an RDF document and convert it to an IR `Model`.

    The format is auto-detected by rdflib from `source_uri`'s extension if
    given, otherwise it's guessed from the bytes. Pass `source_uri` whenever
    you have one — it avoids a guess and keeps the parse deterministic.
    """
    g = Graph()
    fmt = _format_for(source_uri)
    if isinstance(source, bytes):
        g.parse(data=source, format=fmt)
    else:
        g.parse(source=io.StringIO(source), format=fmt)

    version, namespace = _read_model_header(g)
    types = _read_object_types(g)

    return Model(
        version=version,
        namespace=namespace,
        object_types=types,
        source_uri=source_uri,
    )


def _format_for(source_uri: Optional[str]) -> str:
    if not source_uri:
        return "turtle"
    low = source_uri.lower()
    if low.endswith(".jsonld") or low.endswith(".json-ld"):
        return "json-ld"
    if low.endswith(".nt") or low.endswith(".ntriples"):
        return "nt"
    return "turtle"


def _read_model_header(g: Graph) -> tuple[str, str]:
    """Find the (single) forge:Model subject and read its version/namespace."""
    version = "0.0.0"
    namespace = "AgentArmy.Generated"
    for model_node in g.subjects(RDF.type, FORGE.Model):
        v = g.value(model_node, FORGE.version)
        n = g.value(model_node, FORGE.namespace)
        if isinstance(v, Literal):
            version = str(v)
        if isinstance(n, Literal):
            namespace = str(n)
        break
    return version, namespace


def _read_object_types(g: Graph) -> list[ObjectType]:
    """Walk owl:Class subjects, collect their fields + relations."""
    out: list[ObjectType] = []
    # Stable iteration order so a re-parse of the same graph produces the same
    # IR. URIRefs sort lexicographically.
    classes = sorted(
        (c for c in g.subjects(RDF.type, OWL.Class) if isinstance(c, URIRef)),
        key=str,
    )
    for cls in classes:
        ot_name = _local_name(cls)
        field_order = _read_string_list(g, cls, FORGE.fieldOrder)
        relation_order = _read_string_list(g, cls, FORGE.relationOrder)

        # Datatype properties whose domain is this class -> Fields.
        fields_by_name: dict[str, Field] = {}
        for prop in sorted(
            (p for p in g.subjects(RDF.type, OWL.DatatypeProperty) if isinstance(p, URIRef)),
            key=str,
        ):
            if (prop, RDFS.domain, cls) not in g:
                continue
            range_uri = g.value(prop, RDFS.range)
            forge_type = _XSD_TO_FORGE.get(range_uri, "string") if range_uri else "string"
            optional_lit = g.value(prop, FORGE.optional)
            optional = bool(optional_lit and str(optional_lit).lower() == "true")
            default_lit = g.value(prop, FORGE.default)
            default = str(default_lit) if default_lit is not None else None
            fname = _local_name(prop)
            fields_by_name[fname] = Field(
                name=fname,
                type=forge_type,
                optional=optional,
                default=default,
            )

        # Object properties whose domain is this class -> Relations.
        relations_by_name: dict[str, Relation] = {}
        for prop in sorted(
            (p for p in g.subjects(RDF.type, OWL.ObjectProperty) if isinstance(p, URIRef)),
            key=str,
        ):
            if (prop, RDFS.domain, cls) not in g:
                continue
            target_uri = g.value(prop, RDFS.range)
            if not isinstance(target_uri, URIRef):
                continue
            card_lit = g.value(prop, FORGE.cardinality)
            cardinality = str(card_lit) if card_lit else "one"
            inv_lit = g.value(prop, FORGE.inverse)
            inverse = str(inv_lit) if inv_lit else None
            rname = _local_name(prop)
            relations_by_name[rname] = Relation(
                name=rname,
                target=_local_name(target_uri),
                cardinality=cardinality,
                inverse=inverse,
            )

        # Order: explicit forge:fieldOrder/relationOrder wins; lexicographic fallback.
        ordered_fields = _apply_order(field_order, fields_by_name)
        ordered_relations = _apply_order(relation_order, relations_by_name)

        annotations: list[tuple[str, str]] = []
        for ann_pred, ann_obj in g.predicate_objects(cls):
            # Capture rdfs:label / rdfs:comment as annotations; everything else
            # under the forge: namespace except the structural predicates.
            if ann_pred in (RDFS.label, RDFS.comment):
                if isinstance(ann_obj, Literal):
                    annotations.append((str(ann_pred), str(ann_obj)))
            elif str(ann_pred).startswith(str(FORGE)) and ann_pred not in (
                FORGE.fieldOrder,
                FORGE.relationOrder,
            ):
                if isinstance(ann_obj, Literal):
                    annotations.append((str(ann_pred), str(ann_obj)))

        out.append(
            ObjectType(
                name=ot_name,
                fields=tuple(ordered_fields),
                relations=tuple(ordered_relations),
                annotations=tuple(sorted(annotations)),
            )
        )

    return out


def _apply_order(order: list[str], by_name: dict):
    """Place items in `order` first, then any remaining items sorted by name."""
    seen: set[str] = set()
    out = []
    for name in order:
        if name in by_name:
            out.append(by_name[name])
            seen.add(name)
    for name in sorted(by_name):
        if name not in seen:
            out.append(by_name[name])
    return out


def _read_string_list(g: Graph, subject, predicate) -> list[str]:
    """Read an rdf:List under (subject, predicate) as a Python list of strings."""
    head = g.value(subject, predicate)
    if head is None:
        return []
    try:
        items = list(Collection(g, head))
    except Exception:
        return []
    return [str(i) for i in items]


def _local_name(uri: URIRef) -> str:
    """Strip the namespace prefix to get a class/property local name.

    Convention: property URIs may use `ClassName__fieldName` to disambiguate
    when two ObjectTypes share a field name. We strip everything up through
    the last `__` so the IR sees `fieldName`. Class URIs without `__` keep
    their full local segment.
    """
    s = str(uri)
    for sep in ("#", "/"):
        if sep in s:
            s = s.rsplit(sep, 1)[1]
    if "__" in s:
        s = s.rsplit("__", 1)[1]
    return s
