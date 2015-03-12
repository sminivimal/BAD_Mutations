#!/usr/bin/env python

#   The main fetching script.

#   Import Python stdlib packages here
import getpass
import os

#   Import the directory handling script
from lrt_predict.General import dir_funcs
#   Import our file handling script
from lrt_predict.General import file_checks
#   Import the Phytozome signon and URL parsing script
import get_urls
#   Import the downloading script
import fetch_cds
#   Import the BLAST formatting script
import blast_databases

#   A function to perform the fetching
def fetch(base, user, password, fetchonly):
    #   create the base for the LRT
    dir_funcs.makebase(base)
    #   cd into the base. This should work since we already checked the
    #   permissions with the function call above
    os.chdir(base)
    #   Check for a username
    if user:
        pass
    else:
        user = raw_input('Username for JGI Genomes Portal: ')
    #   Check for an entered password, else take it
    if password:
        pass
    else:
        password = getpass.getpass('Password for JGI Genomes Portal: ')
    #   Start a new login session to Phyotozome
    session = get_urls.signon(user, password)
    #   If session is NoneType, then there was a login problem
    if not session:
        print 'There was a problem logging in to JGI Genomes Portal. Check your username and password and try again.'
        exit(1)
    #   Get the list of all URLs and md5s from the downloads tree
    urls, md5s = get_urls.extract_all_urls(session)
    #   Get the CDS only
    cds, md5s_flt = get_urls.extract_cds_urls(urls, md5s)
    #   We will make a list of those that were udpated
    cds_updated = []
    for c, m in zip(cds, md5s_flt):
        #   What is the local name?
        local_name = fetch_cds.local_name(c)
        #   And the species name?
        species_name = fetch_cds.species_name(local_name)
        print 'Fetching ' + species_name + ' ...'
        #   Create the species directory
        spdir = dir_funcs.make_species_dir(base, species_name)
        #   cd into that directory
        os.chdir(spdir)
        #   Do these files exist already?
        print os.path.join(base, spdir, local_name)
        if file_checks.file_exists(local_name):
            #   Calculate the md5
            calc_md5 = file_checks.calculate_md5(local_name)
            #   And then compare
            md5s_same = file_checks.md5_is_same(calc_md5, m)
            #   Then we check if the md5s are the same. If they are the same,
            #   then we skip the file, and move on. Else, we download a new one
            if md5s_same:
                print local_name + ' already exists and MD5s are identical, skipping ...'
                continue
            else:
                print local_name + ' has different MD5 than server. Downloading ...'
                #   A variable to tell if we've sucessfully downloaded the file
                same = False
                while not same:
                    fetch_cds.dl(session, c, local_name)
                    r_md5 = m
                    l_md5 = file_checks.calculate_md5(local_name)
                    same = file_checks.md5_is_same(l_md5, r_md5)
                #   Take the path onto the list of species that need to be made into
                #   BLAST databases
                cds_updated.append(os.path.join(base, spdir, local_name))
        #   If the files don't exist already, then we just download them
        else:
            #   a variable to tell if we've checked out
            same = False
            #   While making sure we downloaded reliably
            while not same:
                fetch_cds.dl(session, c, local_name)
                r_md5 = m
                l_md5 = file_checks.calculate_md5(local_name)
                same = file_checks.md5_is_same(l_md5, r_md5)
            cds_updated.append(os.path.join(base, spdir, local_name))
    print 'Done!'
    return cds_updated


#   A function to handle the conversion to BLAST databases
def convert(base, fname_list):
    #   If the list of filenames is empty, then we will find all gzipped
    #   files by default
    if not fname_list:
        fname_list = file_checks.get_cds_files(base)
    for f in fname_list:
        retval = blast_databases.format_blast(f)
        #   Check the return value
        if retval == 0:
            pass
        else:
            print 'Error! makeblastdb on ' + f + ' returned ' + str(retval)
    return