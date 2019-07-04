# Base

## Test 1 - same file in parallel

### Cached
- 500MB file 2 concurrent requests (`ab -n 100 -c 2 localhost:8080/500MB`)  
3115.150 [ms] (mean, across all concurrent requests)  

- 500MB file 1 concurrent request (`ab -n 50 -c 1 localhost:8080/500MB`)  
3108.204 [ms] (mean, across all concurrent requests)  

### No cache
- 500MB file 2 concurrent requests (`sync; echo 3 | sudo tee /proc/sys/vm/drop_caches; ab -n 2 -c 2 localhost:8080/500MB`)  
5806.631 [ms] (mean, across all concurrent requests)  

- 500MB file 1 concurrent request (`sync; echo 3 | sudo tee /proc/sys/vm/drop_caches; ab -n 1 -c 1 localhost:8080/500MB`)   
8261.821 [ms] (mean, across all concurrent requests)   

## Test 2
- 1GB file concurrent with 100B file (`ab -n 1 -c 1 localhost:8080/1GB > o1 &; sleep 0.0001; ab -n 1 -c 1 localhost:8080/100B > o2`)  
1GB - 6310.641 ms  
100B - 4123.485 ms  

## Test 3
- 1GB file concurrent with response from ram (`ab -n 1 -c 1 localhost:8080/1GB > o1 &; sleep 0.0001; ab -n 1 -c 1 localhost:8080/ram_test > o2`)  
1GB - 6389.014 ms  
ram_test - 4126.474 ms    

# Async read file

## Test 1 - same file in parallel

### Cached
- 500MB file 2 concurrent requests (`ab -n 100 -c 2 localhost:8080/500MB`)  
2980.986 [ms] (mean, across all concurrent requests) 

- 500MB file 1 concurrent request (`ab -n 50 -c 1 localhost:8080/500MB`)  
3129.137 [ms] (mean, across all concurrent requests)

### No cache
- 500MB file 2 concurrent requests (`sync; echo 3 | sudo tee /proc/sys/vm/drop_caches; ab -n 2 -c 2 localhost:8080/500MB`)  
5395.044 [ms] (mean, across all concurrent requests)  

- 500MB file 1 concurrent request (`sync; echo 3 | sudo tee /proc/sys/vm/drop_caches; ab -n 1 -c 1 localhost:8080/500MB`)   
8212.727 [ms] (mean, across all concurrent requests) 

## Test 2
- 1GB file concurrent with 100B file (`ab -n 1 -c 1 localhost:8080/1GB > o1 &; sleep 0.0001; ab -n 1 -c 1 localhost:8080/100B > o2`)  
1GB - 6143.956 ms  
100B - 3.272 ms  

## Test 3
- 1GB file concurrent with response from ram (`ab -n 1 -c 1 localhost:8080/1GB > o1 &; sleep 0.0001; ab -n 1 -c 1 localhost:8080/ram_test > o2`)  
1GB - 6211.032 ms  
ram_test - 1.245 ms  

# Read file in chunks (1000000B)

## Test 1 - same file in parallel

### Cached
- 500MB file 2 concurrent requests (`ab -n 100 -c 2 localhost:8080/500MB`)  
889.894 [ms] (mean, across all concurrent requests)  

- 500MB file 1 concurrent request (`ab -n 50 -c 1 localhost:8080/500MB`)  
909.749 [ms] (mean, across all concurrent requests)

### No cache
- 500MB file 2 concurrent requests (`sync; echo 3 | sudo tee /proc/sys/vm/drop_caches; ab -n 2 -c 2 localhost:8080/500MB`)  
2813.599 [ms] (mean, across all concurrent requests)  

- 500MB file 1 concurrent request (`sync; echo 3 | sudo tee /proc/sys/vm/drop_caches; ab -n 1 -c 1 localhost:8080/500MB`)   
6433.902 [ms] (mean, across all concurrent requests)  

## Test 2
- 1GB file concurrent with 100B file (`ab -n 1 -c 1 localhost:8080/1GB > o1 &; sleep 0.0001; ab -n 1 -c 1 localhost:8080/100B > o2`)  
1GB - 1792.281 ms  
100B - 12.190 ms  

## Test 3
- 1GB file concurrent with response from ram (`ab -n 1 -c 1 localhost:8080/1GB > o1 &; sleep 0.0001; ab -n 1 -c 1 localhost:8080/ram_test > o2`)  
1GB - 1880.590 ms  
ram_test - 1.759 ms  