#! /bin/bash

tables=( "answer" "browser" "codes" "feedback" "fetched" "grades" "lectures" "messages" "notfound" "pages" "post" "roll" "rubrics" "seats" "state" "teams" "worksheet_bonus" "zoom" )
for table in "${tables[@]}"
do
   psql -c "\copy (SELECT * FROM ${table}) TO '${table}.csv' with csv delimiter ',' " mypoll
done

