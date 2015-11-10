#export ARCHIVE_JSON=http://webenact.rhizome.org/collinfo.json
#export ARCHIVE_JSON=/archives.json
docker-compose --x-networking build
docker-compose --x-networking up -d
