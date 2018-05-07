update-cities-db:
	curl -s http://download.geonames.org/export/dump/cities15000.zip | funzip | awk -F '\t' '$$15 > 100000' > tzgrid/cities100000.txt

.PHONY: update-cities-db
