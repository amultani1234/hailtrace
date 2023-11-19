# Hail Trace Project

## Summary

Archive of work done for hailtrace as part of our capstore project. Last updated 2020. The primary task was to stream and process atmospheric radar scans from 160 NEXRAD stations globally to provide soft real-time hail detection.

## Docker

1. Create ```.env``` from ```sample.env```
2. Run ```build.sh```
3. Run ```run.sh```

4. Initialize database collections

```bash
   mongo

   use hailtrace
   
   hailtrace.createCollection('algo_hdr')
   hailtrace.createCollection('algo_mehs')
   hailtrace.createCollection('algo_hsda')
   
   hailtrace.createCollection('log_proc_events')
   hailtrace.createCollection('log_proc_errors')
```

5. Run Tests

```bash
docker exec -it proc /bin/bash
pip3 install pytest
sudo python3 interface.py
```
