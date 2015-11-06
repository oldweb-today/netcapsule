export ARCHIVE_JSON=http://webenact.rhizome.org/collinfo.json
docker-compose --x-networking build
docker-compose --x-networking up -d
