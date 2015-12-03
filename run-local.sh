#export ARCHIVE_JSON=http://webenact.rhizome.org/collinfo.json
export ARCHIVE_JSON=./archives.gen.json
export RANDOM_URL_LIST=./urls.txt
python -c "import yaml; import json; data = yaml.load(open('archives.yaml')); open('$ARCHIVE_JSON', 'w').write(json.dumps(data))"
docker-compose --x-networking build
docker-compose --x-networking up -d
