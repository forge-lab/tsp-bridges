mkdir test$1
for ((id=1;id<=$2;id++ ))
do
  python3 benchmark_generator.py $1 $id 
done 
