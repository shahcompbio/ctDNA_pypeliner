ctdna_pypeliner --input_yaml /home/pye/ctDNA_pypeliner/test_files/bc_saliva.yaml --config /home/pye/ctDNA_pypeliner/config/run024.yaml --umi_trim --tmpdir /shahlab/pye/projects/biof34/run024/tmp --pipelinedir /shahlab/pye/projects/biof34/pipeline/ --submit asyncqsub --nativespec ' -V -hard -q shahlab.q -l h_vmem={mem}G -P shahlab_high -S /bin/bash' --maxjobs 256 --context_config /home/pye/ctDNA_pypeliner/config/context.yaml