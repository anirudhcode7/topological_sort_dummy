#!/bin/bash

pom_file=$1

xmlstarlet sel -N ns="http://maven.apache.org/POM/4.0.0" -t \
  -m "//ns:dependencies/ns:dependency[contains(ns:groupId, 'appviewx')]" \
  -v "ns:artifactId" -n "$pom_file"
