#!/bin/bash

pom_file=$1

value=$(xmlstarlet sel -N ns="http://maven.apache.org/POM/4.0.0" -t \
  -m "//ns:dependencies/ns:dependency[not(ancestor::ns:dependencyManagement) and contains(ns:groupId, 'appviewx')]" \
  -v "ns:artifactId" -n "$pom_file")

echo "$value"
