import pypeliner
import pypeliner.managed as mgd
import deepSNV
import LoLoPicker
import VarScan
import MutationSeq
import Strelka
import union
import tasks
from ctDNA.utils import helpers

def partition_tumour(config, input_args, patient_id, results_dir, input_bams, input_bais, output_file):
    workflow = pypeliner.workflow.Workflow()

    workflow.setobj(obj=mgd.OutputChunks('tumour_id',), value=input_args['tumour_samples'])
    workflow.setobj(obj=mgd.OutputChunks('normal_id',), value=input_args['normal_samples'])

    workflow.transform(
        name='merge_normal',
        func=tasks.merge_normal,
        args=(
            config,
            mgd.InputFile('normal.bam', 'normal_id', fnames=input_args['normal_bams'], axes_origin=[]),
            mgd.OutputFile(input_args['patient_bam_dir'] + 'merged_normal.bam'),
            mgd.OutputFile(input_args['patient_bam_dir'] + 'merged_normal.bam.bai')
            )
        )

    workflow.subworkflow(
        name='analyze_tumour',
        func=analyze_tumour_normal,
        axes=('tumour_id',),
        args=(
            config,
            input_args,
            results_dir,
            mgd.InputFile(input_args['patient_bam_dir'] + 'merged_normal.bam'),
            mgd.InputInstance('tumour_id'),
            mgd.InputFile('tumour.bam', 'tumour_id', fnames=input_bams),
            mgd.OutputFile(results_dir + patient_id + '_{tumour_id}.tsv', 'tumour_id')
            )
        )

    workflow.transform(
        name='log_patient_analysis',
        func=tasks.log_patient_analysis,
        args=(
            mgd.InputFile(results_dir + patient_id + '_{tumour_id}.tsv', 'tumour_id', axes_origin=[]),
            mgd.OutputFile(output_file),
            )
        )

    return workflow

def analyze_tumour_normal(config, input_args, results_dir, normal_bam, tumour_sample, tumour_bam, output_file):
    workflow = pypeliner.workflow.Workflow()

    matched_results_dir = results_dir + '{}/'.format(tumour_sample)

    helpers.makedirs(matched_results_dir)

    workflow.subworkflow(
        name='run_deepSNV',
        func=deepSNV.run_deepSNV,
        args=(
            config,
            mgd.InputFile(normal_bam),
            mgd.InputFile(tumour_bam),
            mgd.OutputFile(matched_results_dir + 'deepSNV_out.tsv')
            )
        )

    workflow.subworkflow(
        name='run_VarScan',
        func=VarScan.run_VarScan,
        args=(
            config,
            mgd.InputFile(normal_bam),
            mgd.InputFile(tumour_bam),
            mgd.OutputFile(matched_results_dir + 'VarScan_out.vcf'),
            ))

    workflow.subworkflow(
        name='run_MutationSeq',
        func=MutationSeq.run_MutationSeq,
        args=(
            config,
            mgd.InputFile(normal_bam),
            mgd.InputFile(tumour_bam),
            mgd.OutputFile(matched_results_dir + 'museq_out.vcf'),
            )
        )

    workflow.subworkflow(
        name='run_Strelka',
        func=Strelka.run_Strelka,
        args=(
            config,
            mgd.InputFile(normal_bam),
            mgd.InputFile(tumour_bam),
            mgd.OutputFile(matched_results_dir + 'strelka_out.vcf'),
            )
        )

    workflow.subworkflow(
        name='run_LoLoPicker',
        func=LoLoPicker.run_LoLoPicker,
        args=(
            config,
            input_args,
            mgd.InputFile(normal_bam),
            mgd.InputFile(tumour_bam),
            mgd.OutputFile(matched_results_dir + 'LoLoPicker_out.tsv'),
            )
        )

    workflow.transform(
        name='create_result_dict',
        func=union.create_result_dict,
        ret=mgd.TempOutputObj('result_dict'),
        args=(
            mgd.InputFile(matched_results_dir + 'deepSNV_out.tsv'),
            mgd.InputFile(matched_results_dir + 'VarScan_out.vcf'),
            mgd.InputFile(matched_results_dir + 'museq_out.vcf'),
            mgd.InputFile(matched_results_dir + 'strelka_out.vcf'),
            mgd.InputFile(matched_results_dir + 'LoLoPicker_out.tsv'),
            )
        )

    workflow.transform(
        name='union_results',
        func=union.union_results,
        args=(
            config,
            mgd.InputFile(normal_bam),
            mgd.InputFile(tumour_bam),
            mgd.TempInputObj('result_dict'),
            mgd.TempSpace('union_space'),
            mgd.OutputFile(output_file),
            ))

    return workflow
