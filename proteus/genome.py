"""This class wraps the indexed FASTA file for an organism's genomic sequence.
It supports retrieving parts of the sequence and converting these parts
into their one hot encodings.
"""
import logging
from time import time

import numpy as np
from pyfaidx import Fasta


LOG = logging.getLogger("deepsea")


def _sequence_to_encoding(sequence, bases_encoding):
    """Converts an input sequence to its one hot encoding.

    Parameters
    ----------
    sequence : str
        The input sequence of length N.

    Returns
    -------
    numpy.ndarray, dtype=bool
        The N-by-4 encoding of the sequence.
    """
    t_i = time()
    encoding = np.zeros((len(sequence), 4))
    sequence = str.upper(sequence)
    for index, base in enumerate(sequence):
        if base in bases_encoding:
            encoding[index, bases_encoding[base]] = 1
        else:
            encoding[index, :] = 0.25
    #print("_sequence_to_encoding: {0}".format(time() - t_i))
    return encoding

def _encoding_to_sequence(encoding, bases_arr):
    t_i = time()
    sequence = []
    for row in encoding:
        base_pos = np.where(row == 1)[0]
        if len(base_pos) != 1:
            sequence.append('N')
        else:
            sequence.append(bases_arr[base_pos[0]])
    #print("_enc_to_seq: {0}".format(time() - t_i))
    return "".join(sequence)

def _get_sequence_from_coords(len_chrs, genome_sequence,
                             chrom, start, end, strand='+'):
    """Gets the genomic sequence given the chromosome, sequence start,
    sequence end, and strand side.

    Parameters
    ----------
    chrom : str
        e.g. "chr1".
    start : int
    end : int
    strand : {'+', '-'}, optional
        Default is '+'.

    Returns
    -------
    str
        The genomic sequence.

    Raises
    ------
    ValueError
        If the input char to `strand` is not one of the specified choices.
    """
    if start > len_chrs[chrom] or end > len_chrs[chrom] \
            or start < 0:
        return ""

    if strand == '+':
        return genome_sequence(chrom, start, end, strand)
    elif strand == '-':
        return genome_sequence(chrom, start, end, strand)
    else:
        raise ValueError(
            "Strand must be one of '+' or '-'. Input was {0}".format(
                strand))


class Genome(object):

    BASES_ARR = np.array(['A', 'C', 'G', 'T'])
    BASES_DICT = dict(
        [(base, index) for index, base in enumerate(BASES_ARR)])

    def __init__(self, fa_file):
        """Wrapper class around the pyfaix.Fasta class.

        Parameters
        ----------
        fa_file : str
            Path to an indexed FASTA file, that is, a *.fasta file with a
            corresponding *.fai file in the same directory.
            File should contain the target organism's genome sequence.

        Attributes
        ----------
        genome : Fasta
        chrs : list[str]
        len_chrs : dict
            The length of each chromosome sequence in the file.
        """
        self.genome = Fasta(fa_file)
        self.chrs = sorted(self.genome.keys())
        self.len_chrs = self._get_len_chrs()

    def _get_len_chrs(self):
        """Gets the length of each chromosome sequence in the file.
        `self.len_chrs` is used for quick lookup of this information
        during sampling.
        """
        len_chrs = {}
        for chrom in self.chrs:
            len_chrs[chrom] = len(self.genome[chrom])
        return len_chrs

    def _genome_sequence(self, chrom, start, end, strand='+'):
        if strand == '+':
            return self.genome[chrom][start:end].seq
        else:
            return self.genome[chrom][start:end].reverse.complement.seq

    def get_sequence_from_coords(self, chrom, start, end, strand='+'):
        """Gets the genomic sequence given the chromosome, sequence start,
        sequence end, and strand side.

        Parameters
        ----------
        chrom : str
            e.g. "chr1".
        start : int
        end : int
        strand : {'+', '-'}, optional
            Default is '+'.

        Returns
        -------
        str
            The genomic sequence.

        Raises
        ------
        ValueError
            If the input char to `strand` is not one of the specified choices.
        """
        return _get_sequence_from_coords(
            self.len_chrs, self._genome_sequence, chrom, start, end, strand)

    def get_encoding_from_coords(self, chrom, start, end, strand='+'):
        """Gets the genomic sequence given the chromosome, sequence start,
        sequence end, and strand side; and return its one hot encoding.

        Parameters
        ----------
        chrom : str
            e.g. "chr1".
        start : int
        end : int
        strand : {'+', '-'}, optional
            Default is '+'.

        Returns
        -------
        numpy.ndarray, dtype=bool
            The N-by-4 encoding of the sequence.

        Raises
        ------
        ValueError
            If the input char to `strand` is not one of the specified choices.
            (Raised in the call to `self.get_sequence_from_coords`)
        """
        sequence = self.get_sequence_from_coords(chrom, start, end, strand)
        encoding = self.sequence_to_encoding(sequence)
        return encoding

    def sequence_to_encoding(self, sequence):
        """Converts an input sequence to its one hot encoding.

        Parameters
        ----------
        sequence : str
            The input sequence of length N.

        Returns
        -------
        numpy.ndarray, dtype=bool
            The N-by-4 encoding of the sequence.
        """
        return _sequence_to_encoding(sequence, self.BASES_DICT)

    def encoding_to_sequence(self, encoding):
        return _encoding_to_sequence(encoding, self.BASES_ARR)
