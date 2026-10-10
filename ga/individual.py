from constants import *
from genotype import Genotype

class Individual:
    """
    Representa um indivíduo da população.

    Um indivíduo possui um genótipo completo, composto por:
        - 4 padrões de bateria (BatI, Bat1, Bat2 e BatF)
        - 8 genes, sendo um para cada colcheia do compasso
        - 8 acordes harmônicos consecutivos
        - 2 padrões de baixo
        - 2 padrões de arpejo
        - 2 padrões de melodia, cada um com 8 compassos
    """

    def __init__(self, genotype=None):
        self.genotype = (
            Genotype()
            if genotype is None
            else genotype
        )

    @property
    def bat1(self):
        return self.genotype.bat1

    @property
    def bat2(self):
        return self.genotype.bat2

    @property
    def bati(self):
        return self.genotype.bati

    @property
    def batf(self):
        return self.genotype.batf

    @property
    def bass_patt1(self):
        return self.genotype.bass_patt1

    @bass_patt1.setter
    def bass_patt1(self, value):
        self.genotype.bass_patt1 = value

    @property
    def bass_patt2(self):
        return self.genotype.bass_patt2

    @bass_patt2.setter
    def bass_patt2(self, value):
        self.genotype.bass_patt2 = value

    @property
    def arp_patt1(self):
        return self.genotype.arp_patt1

    @arp_patt1.setter
    def arp_patt1(self, value):
        self.genotype.arp_patt1 = value

    @property
    def arp_patt2(self):
        return self.genotype.arp_patt2

    @arp_patt2.setter
    def arp_patt2(self, value):
        self.genotype.arp_patt2 = value

    @property
    def mel_patt1(self):
        return self.genotype.mel_patt1

    @mel_patt1.setter
    def mel_patt1(self, value):
        self.genotype.mel_patt1 = value

    @property
    def mel_patt2(self):
        return self.genotype.mel_patt2

    @mel_patt2.setter
    def mel_patt2(self, value):
        self.genotype.mel_patt2 = value

    @property
    def bass_pattern(self):
        return self.genotype.bass_patt1

    @bass_pattern.setter
    def bass_pattern(self, value):
        self.genotype.bass_patt1 = value

    @property
    def mchord1(self):
        return self.genotype.mchord1

    @mchord1.setter
    def mchord1(self, value):
        self.genotype.mchord1 = value

    @property
    def mchord2(self):
        return self.genotype.mchord2

    @mchord2.setter
    def mchord2(self, value):
        self.genotype.mchord2 = value

    @property
    def mchord3(self):
        return self.genotype.mchord3

    @mchord3.setter
    def mchord3(self, value):
        self.genotype.mchord3 = value

    @property
    def mchord4(self):
        return self.genotype.mchord4

    @mchord4.setter
    def mchord4(self, value):
        self.genotype.mchord4 = value

    @property
    def mchord5(self):
        return self.genotype.mchord5

    @mchord5.setter
    def mchord5(self, value):
        self.genotype.mchord5 = value

    @property
    def mchord6(self):
        return self.genotype.mchord6

    @mchord6.setter
    def mchord6(self, value):
        self.genotype.mchord6 = value

    @property
    def mchord7(self):
        return self.genotype.mchord7

    @mchord7.setter
    def mchord7(self, value):
        self.genotype.mchord7 = value

    @property
    def mchord8(self):
        return self.genotype.mchord8

    @mchord8.setter
    def mchord8(self, value):
        self.genotype.mchord8 = value

    def __repr__(self):
        return (
            f"Individual("
            f"bat1={self.bat1}, "
            f"mchords={self.genotype.mchords})"
        )
