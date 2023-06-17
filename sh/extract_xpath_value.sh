#!/bin/bash

pom_file=$1
xpath_expression=$2

value=$(xmlstarlet sel -N ns="http://maven.apache.org/POM/4.0.0" -t -m "$xpath_expression" -v . -n "$pom_file")
echo "$value"
