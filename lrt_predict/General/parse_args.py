#!/usr/bin/env python
#   Helper script for Phytozome.py
#   Contains argument parsing code

import argparse
import os
import getpass

#   Import the helper script to validate arguments
import check_args
#   And the script to check the input files
import parse_input
#   And the script to operate on files
import file_funcs
#   And the script to check the configuration file
from ..Setup import parse_config
#   And the species lists
from ..Fetch import ensembl_species
from ..Fetch import phytozome_species

#   Create the list of allowable species by the combination of both
#   Phytozome and Ensembl. Currently this is restricted to angiosperms
allowable_species = ensembl_species.ensembl_fetch + phytozome_species.phyto_fetch

#   A function to actually parse the arguments
def parse_args():
    parser = argparse.ArgumentParser(
        description = 'LRT for deleterious SNP prediction in plants.',
        add_help=True)
    #   Define a sub-parser to handle the different actions we can perform
    #   we can either 'fetch' or 'predict'
    subparser = parser.add_subparsers(
        dest='action',
        title='Available actions',
        help='Sub-command help')

    #   Create a parser for 'setup'
    setup_args = subparser.add_parser(
        'setup',
        help='Set up the runtime environment of LRT_Predict')
    setup_args.add_argument(
        '--list-species',
        required=False,
        action='store_true',
        default=False,
        help='List the accepted names of query species (case sensitive).')
    setup_args.add_argument(
        '--config',
        '-c',
        required=False,
        help='Where to store the configuration file.',
        default=os.path.join(os.getcwd(), 'LRTPredict_Config.txt'))
    setup_args.add_argument(
        '--base',
        '-b',
        required=False,
        help='Base directory for species databases. Defaults to .',
        default=os.getcwd())
    setup_args.add_argument(
        '--target',
        '-t',
        required=False,
        help='Which species are you predicting in (case sensitive)? Pass --list-species to see a full list of allowable species names.',
        default=None)
    setup_args.add_argument(
        '--evalue',
        '-e',
        required=False,
        default=0.05,
        type=float,
        help='E-value threshold for accepting sequences into the alignment.')
    setup_args.add_argument(
        '-m',
        '--missing_threshold',
        required=False,
        type=float,
        default=0.25,
        help='Skip predictions for sites with at least this much missing data (gaps) in the multiple sequence alignment.')
    setup_args.add_argument(
        '-codon',
        required=False,
        action='store_const',
        const='-codon',
        default='-translate',
        help='Use the codon alignment model for prank-msa, may give more accurate branch lengths but is much slower.')

    #   Create a parser for 'fetch'
    fetch_args = subparser.add_parser(
        'fetch',
        help='Fetch CDS files from Phytozome and Ensembl')
    #   And give it some arguments
    fetch_args.add_argument(
        '--config',
        '-c',
        required=False,
        help='Use this configuration file.')
    fetch_args.add_argument(
        '--base',
        '-b',
        required=False,
        help='Base directory for species databses.')
    fetch_args.add_argument(
        '--user',
        '-u',
        required=False,
        default=None,
        help='Username for jgi.doe.gov (For fetching from Phytozome)')
    fetch_args.add_argument(
        '--password',
        '-p',
        required=False,
        help='Password for jgi.doe.gov. If you are not comfortable supplying\
        this on the command-line in text, you can enter it on the prompt.',
        default=None)
    #   Create a new mutually exclusive group for deciding if we want to only
    #   fetch, or if we want to convert
    actions = fetch_args.add_mutually_exclusive_group(required=False)
    actions.add_argument(
        '--fetch-only',
        required=False,
        action='store_true',
        default=False,
        help='Do not convert CDS files to BLAST databases, just fetch.')
    actions.add_argument(
        '--convert-only',
        required=False,
        action='store_true',
        default=False,
        help='Do not fetch new CDS from databases, just convert to BLAST db.')

    #   Create a parser for 'predict'
    predict_args = subparser.add_parser(
        'predict',
        help='Run the LRT prediction pipeline.')
    predict_args.add_argument(
        '--config',
        '-c',
        required=False,
        help='Use this configuration file.')
    #   Give 'predict' some arguments
    predict_args.add_argument(
        '--base',
        '-b',
        required=False,
        help='Base directory for species databses.')
    predict_args.add_argument(
        '--fasta',
        '-f',
        required=True,
        default=None,
        help='Path to the input FASTA file.')
    predict_args.add_argument(
        '--substitutions',
        '-s',
        required=True,
        default=None,
        help='Path to the input substitutions file.')
    predict_args.add_argument(
        '--evalue',
        '-e',
        required=False,
        default=0.05,
        type=float,
        help='E-value threshold for accepting sequences into the alignment.')
    predict_args.add_argument(
        '-codon',
        required=False,
        action='store_const',
        const='-codon',
        default='-translate',
        help='Use the codon alignment model for prank-msa, may give more accurate branch lengths but is much slower.')
    #   Add a switch for verbosity
    parser.add_argument(
        '--verbosity',
        '-v',
        required=False,
        dest='loglevel',
        choices = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        default='INFO',
        help='Minimum verbosity level of messages printed.')
    args = parser.parse_args()
    return args


#   Here we validate the arguments
def validate_args(args, log):
    #   Check the base argument. If it starts with something other than a /
    #   then it is a relative path, and we should fix it
    if not args['base'].startswith('/'):
        #   Add the cwd onto it, since the script fails otherwise
        args['base'] = os.path.join(os.getcwd(), args['base'])
    #   Then check the action
    #   If we are fetching, we have to check the username and base
    #   argparse should have checked for missing arguments by now
    #   If the arguments do not check out, return a message
    if args['action'] == 'setup':
        if args['list_species']:
            return (False, 'The list of allowable species names is \n' + '\n'.join(allowable_species))
        if args['target'] not in allowable_species:
            return (False, 'The species name you provided is not in the list of allowable species.')
        if not check_args.valid_dir(os.path.dirname(args['config'])):
            return (False, 'You cannot create a configuration file in that directory.')
        if not check_args.valid_dir(args['base']):
            return (False, 'Base directory is not readable/writable, or does not exist.')
    elif args['action'] == 'fetch':
        #   If config is suppled:
        if args['config']:
            if not file_funcs.file_exists(args['config'], log):
                return (False, 'The specified configuration file does not exist!')
        #   If username is supplied:
        if args['user']:
            #   Check if it's valid
            if not check_args.valid_email(args['user']):
                return (False, 'Username is not a valid e-mail address.')
        #   Username not supplied, and we need to access JGI
        elif not args['convert_only']:
            args['user'] = raw_input('Username for JGI Genomes Portal: ')
        #   Else, we only want to convert
        else:
            pass
        #   Same with password
        if args['password']:
            pass
        elif not args['convert_only']:
            args['password'] = getpass.getpass('Password for JGI Genomes Portal: ')
        else:
            pass
        if not check_args.valid_dir(args['base']):
            return (False, 'Base directory is not readable/writable, or does not exist.')
        else:
            pass
    #   Check arguments to predict
    elif args['action'] == 'predict':
        #   If config is suppled:
        if args['config']:
            if not file_funcs.file_exists(args['config'], log):
                return (False, 'The specified configuration file does not exist!')
        if not parse_input.valid_fasta(args['fasta'], log):
            return (False, 'The input FASTA file provided is not valid.')
            exit(1)
        if not parse_input.parse_subs(args['substitutions'], log):
            return (False, 'The input substitutions file provided is not valid.')
            exit(1)
    return (args, None)


#   This is just a simple function that shows when the user does not supply
#   any arguments. This is an issue with Python 2.*, and has been "fixed" in
#   Python 3+.
def usage():
    print '''Usage: LRT_Predict.py <subcommand> <arguments>

where <subcommand> is one of 'setup', 'fetch', or 'predict.' This script will
download the necessary data to perform the likelihood ratio test (LRT) for
deleterious SNP prediction as described in Chun and Fay (2009) in Genome 
Research. Because of the data sources used, this implementation is specific to
SNP annotation in plants.

The 'setup' subcommand will create a configuration file that contains paths to
requried executables and parameters for alignment. This is optional, but
recommended, as it makes batches of analysis much easier to standardize.

The 'fetch' subcommand will download gzipped CDS FASTA files from Phytozome, 
unzip them, and convert them into BLAST databases. It requires a (free) username
and password for the JGI Genomes Portal. Check with Phytozome for their data
release and usage policies. Use 'LRT_Predict.py fetch -h' for more information.

The 'predict' subcommand will run the LRT with a given query sequence and a
list of affected codons. This feature has not yet been implemented.

Dependencies:
    Biopython
    tblastx (NCBI BLAST executables)
    requests (Python HTTP requests module)
    prank-msa (Phylogeny-aware sequence alignment)'''
    return
