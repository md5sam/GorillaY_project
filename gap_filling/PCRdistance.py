#!/usr/local/bin/python
# fill gaps in scaffolds based on reference (e.g. human) 
#python walkAssembly.py genesHumanBiomartY.list genes_on_assembly.sam genesHumanBiomartY.fasta assembly_in_fasta
import sys
import test
import os
import re
import subprocess
from Bio import SeqIO
from collections import defaultdict

SAMdict = defaultdict(list)

class GeneMappings:
    """Class that for every gene stores where it maps"""
    def __init__(self, name, start, end, orientation, mappings, number_of_mappings, flagstat, mapping_positions,length):
        self.name = name
        self.start = start
        self.end = end
        self.orientation = orientation
        self.mappings = mappings
        self.number_of_mappings=number_of_mappings
        self.flagstat = flagstat
        self.mapping_positions = mapping_positions
        self.length = length

def parseSAM(file):
    for line in open(file):
        li=line.strip()
        if not li.startswith("@SQ"):
            SAMline=line.rstrip()
            #print SAMline
            fields=SAMline.split()
            gene=fields[0]
            flag=fields[1]
            mappings=fields[2]
            pos=fields[3]
            array=[flag,mappings,pos]
            SAMdict[gene].append(array)
            print ("GENE: " + gene + " FLAG: " + flag + " MAPPINGS: " + mappings + " POS: " + pos)

gene_file = sys.argv[1]
sam_file = sys.argv[2]
fasta_file = sys.argv[3]
assembly_file = sys.argv[4]

print ("gene file: " + gene_file)
print ("sam file: " + sam_file)

output_file = sam_file + "_gapFilling"

toWalk=open(output_file+".txt", "w")
toWalkFasta=open(output_file+".fasta", "w")
toWalkStat=open(output_file+".stat.txt", "w")

handle = open(fasta_file, "rU")
record_dict = SeqIO.to_dict(SeqIO.parse(handle, "fasta"))
handle.close()

handle = open(assembly_file, "rU")
record_assembly = SeqIO.to_dict(SeqIO.parse(handle, "fasta"))
handle.close()

parseSAM(sam_file)
print SAMdict

#for every gene in order of humanY
with open(gene_file, "r") as outer:
        ROUND=0
        for outerline in outer:
            ROUND=ROUND+1
            print ("ROUND: " + str(ROUND))

            array=outerline.split('\t')
            gene=array[4]
            gene=gene.rstrip('\n')

            #gene_array=getMappingsForGene(gene)
            #SAM_array contains FLAG MAPPING POS
            #print SAMdict[gene]
            SAM_array=(SAMdict[gene])[0]

            #upload only first mapping, but update the information about number of mappings available
            l=int(array[2])-int(array[1])+1
            geneOuter=GeneMappings(name=gene, start=int(array[1]), end=int(array[2]), orientation=int(array[3]), mappings=SAM_array[1], number_of_mappings=len(SAMdict[gene]), flagstat=int(SAM_array[0]), mapping_positions=SAM_array[2], length=l)


            with open(gene_file, "r") as inner:
                for innerline in inner:
                    array=innerline.split('\t')
                    gene=array[4]
                    gene=gene.rstrip('\n')

                    #gene_array=getMappingsForGene(gene)
                    #SAM_array contains FLAG MAPPING POS
                    #print SAMdict[gene]
                    SAM_array=(SAMdict[gene])[0]

                    #upload only first mapping, but update the information about number of mappings available
                    l=int(array[2])-int(array[1])+1
                    geneInner=GeneMappings(name=gene, start=int(array[1]), end=int(array[2]), orientation=int(array[3]), mappings=SAM_array[1], number_of_mappings=len(SAMdict[gene]), flagstat=int(SAM_array[0]), mapping_positions=SAM_array[2], length=l)

                    #look up contigs in fasta 
                    outer_contig=geneOuter.mappings
                    inner_contig=geneInner.mappings

                    if (geneOuter.number_of_mappings + geneInner.number_of_mappings == 2 ) and (geneOuter.mappings != geneInner.mappings) and (outer_contig != "*") and (inner_contig != "*") and (geneOuter.end <= geneInner.start):

                        print ("outer gene: " + geneOuter.name + " innner gene: " + geneInner.name)

                        #retrieve assembly sequences
                        outer_record=record_assembly[outer_contig] #use any record ID
                        inner_record=record_assembly[inner_contig]

                        #calculate distance between contigs
                        #first calculate distance between genes

                        #lengths of contigs
                        length_of_outer_contig=int(len(outer_record.seq))
                        length_of_inner_contig=int(len(inner_record.seq))

                        print ("length_of_outer_contig: " + str(length_of_outer_contig) + " length_of_inner_contig: " + str(length_of_inner_contig))


                        PCRdistanceBetweenGenes=geneInner.start - geneOuter.end #this distance is over-estimation of real distance, we need to subtract distances of the genes to the end of contigs
                        print ("gene distance estimate: " + str(PCRdistanceBetweenGenes))

                        if (PCRdistanceBetweenGenes>500000):
                            print ("current gene too distant from outer gene, trying new outer gene; break;")
                            break;
                            print ("-----------------------------------------------------------------------")

                        #subtract distance of geneA to the end of contig
                        distance_to_the_end_of_first_contig=(length_of_outer_contig-int(geneOuter.mapping_positions)+int(geneOuter.length))
                        PCRdistanceEstimate=PCRdistanceBetweenGenes-distance_to_the_end_of_first_contig

                        #substract distance of geneB to the beginning of contig
                        distance_to_the_start_of_gene_at_second_contig=int(geneInner.mapping_positions)
                        PCRdistanceEstimate=PCRdistanceEstimate-distance_to_the_start_of_gene_at_second_contig

                        print ("distance_to_the_end_of_first_contig: " + str(distance_to_the_end_of_first_contig) + " distance_to_the_start_of_gene_at_second_contig: " + str(distance_to_the_start_of_gene_at_second_contig))

                        print ("PCR distance estimate: " + str(PCRdistanceEstimate))

                        if ((PCRdistanceEstimate<=20000) and (PCRdistanceEstimate>-10000)):
                            print (str(PCRdistanceEstimate) + " PCR product size OK")
                            print outerline
                            print vars(geneOuter)
                            print innerline
                            print vars(geneInner)

                            #check for orientation
                            print (str(geneOuter.orientation) + " " + str(geneInner.orientation))
                            orientation_score=geneInner.orientation+geneOuter.orientation
                            print ("orientation_score: " + str(orientation_score))

                            print ("outer flagstat: " + str(geneOuter.flagstat) + " flagstat: " + str(geneInner.flagstat))

                            #reverse complement if needed
                            if ((geneOuter.orientation==1) and (geneInner.orientation==1)):
                                human_orientation="sense sense"
                                print human_orientation
                                #both in sense orientation in human, so both need to be in sense orientation in contigs
                                if (geneOuter.flagstat==16):
                                    outer_record.seq=(outer_record.seq).reverse_complement()
                                    print "reverse complementing outer gene"
                                if (geneInner.flagstat==16):
                                    inner_record.seq=(inner_record.seq).reverse_complement()
                                    print "reverse complementing gene"

                            if ((geneOuter.orientation==-1) and (geneInner.orientation==-1)):
                                human_orientation="antisense sense"
                                print human_orientation
                                #both in reverse orientation in human, so both need to be in reverse orientation in contigs
                                if (geneOuter.flagstat==0):
                                    outer_record.seq=(outer_record.seq).reverse_complement()
                                    print "reverse complementing outer gene"
                                if (geneInner.flagstat==0):
                                    inner_record.seq=(inner_record.seq).reverse_complement()
                                    print "reverse complementing gene"

                            if ((geneOuter.orientation==1) and (geneInner.orientation==-1)):
                                human_orientation="sense antisense"
                                print human_orientation
                                if (geneOuter.flagstat==16):
                                    outer_record.seq=(outer_record.seq).reverse_complement()
                                    print "reverse complementing outer gene"
                                if (geneInner.flagstat==0):
                                    inner_record.seq=(inner_record.seq).reverse_complement()
                                    print "reverse complementing gene"

                            if ((geneOuter.orientation==-1) and (geneInner.orientation==1)):
                                human_orientation="antisense sense"
                                print human_orientation
                                #both in sense orientation in human, so both need to be in sense orientation in contigs
                                if (geneOuter.flagstat==0):
                                    outer_record.seq=(outer_record.seq).reverse_complement()
                                if (geneInner.flagstat==16):
                                    inner_record.seq=(inner_record.seq).reverse_complement()

                            #retrieve updated sequences
                            outer_fasta=("\n>" + outer_record.id + "\n" + outer_record.seq)
                            inner_fasta=("\n>" + inner_record.id + "\n" + inner_record.seq)

                            candidate_report="\nCANDIDATE " + geneOuter.name + " maps to " + geneOuter.mappings + " at " + geneOuter.mapping_positions + "bp AND " + geneInner.name + " maps to " + geneInner.mappings + " at " + geneInner.mapping_positions + "bp; distance_between_genes is: " + str(PCRdistanceBetweenGenes) + "; PCR product size is: " + str(PCRdistanceEstimate) + "; distance_from_gene_to_end_of_first_contig: " + str(distance_to_the_end_of_first_contig) + " distance_to_start_of_gene_at_second_contig: " + str(distance_to_the_start_of_gene_at_second_contig) + "; length_of_first_contig: " + str(length_of_outer_contig) + "; length_of_second_contig: " + str(length_of_inner_contig) + " first_gene_length: " + str(geneOuter.length) + " second_gene_length: " + str(geneInner.length) + " ; human_orientation: "  + human_orientation;
                            
                            print candidate_report; 
                            toWalk.write(str(candidate_report) + str(outer_fasta) + str(inner_fasta))

                            #retrieve genes
                            outer_record_genes=record_dict[geneOuter.name] #use any record ID
                            inner_record_genes=record_dict[geneInner.name]
                        
                            outer_fasta_gene=(">" + outer_record_genes.id + "\n" + outer_record_genes.seq)
                            inner_fasta_gene=(">" + inner_record_genes.id + "\n" + inner_record_genes.seq)
                            
                            gene_report=("\n" + outer_fasta_gene + "\n" + inner_fasta_gene + "\n----------")
                            print (gene_report)
                            toWalk.write(str(gene_report))
                            toWalkFasta.write(str(outer_fasta) + str(inner_fasta))
                            toWalkStat.write(str(candidate_report) + "\n")
                        else:
                            print (str(PCRdistanceEstimate) + " PCR product size NOK")

                    #else:
                        #print (" NOT CANDIDATE")

# Close opened file
toWalk.close()
toWalkFasta.close()
toWalkStat.close()




