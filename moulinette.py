#!/usr/bin/env python3
import sys
import os
import platform
from colorama import init, Fore

ESPACES_PAR_TABULATION = 8

auteurs = []

class Norme(object):
    """Verifie la norme d'un fichier"""
    def __init__(self, nom_fichier):
        self.nom_fichier = nom_fichier
        self.f = 0
        self.lines = []
        self.nb_lignes = 0
        self.erreurs = []
        self.dangers = []
        self.nom_afficher = 0

    def reporter_erreur(self, msg, ligne):
        self.erreurs.append(Fore.RED + "\tErreur: " + Fore.YELLOW
                            + msg + Fore.RED + " ligne " + str(ligne)
                            + Fore.RESET)
        # print (self.nom_fichier)
        # print (Fore.RED + msg + " line " + str(ligne) + Fore.RESET)
        return -1

    def reporter_danger(self, msg, ligne):
        self.dangers.append(Fore.YELLOW + "\tDanger: "
                            + msg + " ligne " + str(ligne)
                            + Fore.RESET)
        # print (self.nom_fichier)
        # print (Fore.YELLOW + msg + " line " + str(ligne) + Fore.RESET)
        return -1

    def afficher_erreurs(self):
        if self.nom_afficher == 0 and len(self.erreurs) > 0:
            print (self.nom_fichier)
            self.nom_afficher = 1
        for erreur in self.erreurs:
            print (erreur)

    def afficher_dangers(self):
        if self.nom_afficher == 0 and len(self.dangers) > 0:
            print (self.nom_fichier)
            self.nom_afficher = 1
        for danger in self.dangers:
            print (danger)

    def nombres_erreurs_et_dangers(self):
        return len(self.erreurs) + len(self.dangers)

    def ajouter_auteur(self, nom):
        if nom not in auteurs:
            auteurs.append(nom)

    def inspecter_nombre_colonnes(self):
        for index, line in enumerate(self.lines):
            size = len(line.expandtabs(ESPACES_PAR_TABULATION))
            if size > 80:
                self.reporter_erreur("Ligne de " + str(size) + " colonnes", index + 1)

    def inspecter_nombre_instruction(self):
        chaines = False
        for index, line in enumerate(self.lines):
            strtab = line.split()
            if line.count(';') > 1 and strtab[0] != "for":
                n_inst = 0
                for c in line:
                    if c == '"':
                        chaines = not chaines
                    if c == ';' and chaines == False:
                        n_inst += 1
                if n_inst > 1:
                    self.reporter_erreur("Nombres d'instructions > 1", index + 1)

    def inspecter_entete(self):
        if self.nb_lignes < 9:
            return self.reporter_erreur("Entete manquante", 1)
        if self.lines[0] != "/*\n":
            return self.reporter_erreur("Entete manquante, ou pas a la 1ere ligne (ouais j'suis chiant)", 1)
        for i in range(1, 8):
            if self.lines[i].startswith("**") == False:
                self.reporter_erreur("Entete: debut de ligne different de \"**\"", i)
        if self.lines[8] != "*/\n":
            self.reporter_erreur("Fin de l'entete bidon (\"*/\" attendu)", 9)
        if len(self.lines[1].split()) < 6:
            self.reporter_danger("Seconde ligne de l'entete pas conforme: \"FICHIER for PROJET in REPERTOIRE\" ", 2)
        else:
            if self.nom_fichier.endswith(self.lines[1].split()[1]) == False:
                self.reporter_danger("Nom de fichier dans l'entete different du vrai nom de fichier", 2)
            if "/home/" in self.lines[1].split()[5]:
                self.ajouter_auteur(self.lines[1].split()[5].split('/')[2])
        if len(self.lines[3].split()) < 4:
            self.reporter_danger("Quatrieme ligne de l'entete pas conforme: \"Made by TROU_DU_CUL\" ", 2)
        else:
            self.ajouter_auteur(self.lines[3].split()[3])
        if len(self.lines[4].split()) < 3:
            self.reporter_danger("Cinquieme ligne de l'entete pas conforme: \"Login TROU@DANS_TON_CUL\" ", 2)
        if len(self.lines[6].split()) < 9:
            self.reporter_danger("Septieme ligne de l'entete pas conforme: \"Started on [la suite]\" ", 2)
        else:
            self.ajouter_auteur(self.lines[6].split()[8])
        if len(self.lines[7].split()) < 9:
            self.reporter_danger("Huitieme ligne de l'entete pas conforme: \"Last [la suite]\" ", 2)
        else:
            self.ajouter_auteur(self.lines[7].split()[8])

    def inspecter_macro_temoin(self):
        i = 0
        if platform.system() == "Windows":
            macro_attendue = self.nom_fichier.upper().split('\\')[-1].split('.')[0] + "_H_"
        else:
            macro_attendue = self.nom_fichier.upper().split('/')[-1].split('.')[0] + "_H_"
        macro_temoin = []
        while i < len(self.lines) and self.lines[i].startswith("#ifndef ") == False:
            i += 1
        if i == len(self.lines) or len(self.lines[i].split()) < 2:
            return self.reporter_erreur("Pas de macro temoin", i + 1)
        macro_temoin = self.lines[i].split()[1]
        if macro_temoin != macro_attendue:
            return self.reporter_erreur("Macro temoin differente de celle attendue (" + macro_attendue + ")", i + 1)
        if self.lines[i + 1].startswith("# define") == False or len(self.lines[i + 1].split()) < 3:
            return self.reporter_erreur("#ifndef doit etre suivi de \"# define \" sur la ligne suivante", i + 2)
        if self.lines[i + 1].split()[2] != macro_temoin:
            return self.reporter_erreur("Deux macros temoins differentes", i + 2)
        while i < len(self.lines) and self.lines[i].startswith("#endif /* !" + macro_temoin + " */") == False:
            i += 1
        if i == len(self.lines):
            return self.reporter_erreur("Pas de #endif pour la macro temoin, ou mal formate: \"#endif /* !MACRO /*\"", i + 1)

    def recuperer_fin_fonction(self, index_debut):
        for index, line in enumerate(self.lines):
            if index > index_debut and line[0] == '}':
                return index
        return 0

    def inspecter_nombre_ligne_par_fonction(self):
        for index, line in enumerate(self.lines):
            if index > 0 and line[0] == '{' and self.lines[index - 1].split()[-1] != '=':
                fin_fonction = self.recuperer_fin_fonction(index)
                nb_lignes = fin_fonction - index - 1
                if nb_lignes > 25:
                    self.reporter_erreur("Fonction de " + str(nb_lignes) + " lignes", index + 1)

    def inspecter_nombre_fonctions(self):
        nb_fonctions = 0
        keyword = ["typedef", "enum", "struct", "union"]
        for index, line in enumerate(self.lines):
            if (index > 0 and line[0] == '{'
                and self.lines[index - 1].split()[-1] != '='
                and self.lines[index - 1].split()[0] not in keyword):
                nb_fonctions += 1
        if nb_fonctions > 5:
            self.reporter_erreur(str(nb_fonctions) + " fonctions dans le fichier", 1)

    def inspecter_macro_multilignes(self):
        for index, line in enumerate(self.lines):
            strtab = line.split()
            if len(strtab) > 0 and strtab[0] == '#' and strtab[1].upper() == "define" and strtab[-1] == '\\':
                self.reporter_erreur("Macro multilignes", index + 1)

    def inspecter_fonctions_dans_header(self):
        keyword = ["return", "while", "for", "if"]
        for index, line in enumerate(self.lines):
            for key in keyword:
                if key in line.split() and line.startswith("**") == False:
                    self.reporter_danger("Il semble que t'ai mis du code dans un fichier header: "
                                         + "utilisation du mot clef " + key, index + 1)
                if '(' in line and ')' in line and 'DEFINE' not in line.upper() and ';' not in line:
                    if index == 0:
                        self.reporter_danger("Il semble que t'ai mis du code dans un fichier header", index + 1)
                    elif (len(self.lines[index - 1]) > 0
                    and len(self.lines[index - 1].split()) > 0
                    and self.lines[index - 1].split()[-1] != '\\'):
                        self.reporter_danger("Il semble que t'ai mis du code dans un fichier header", index + 1)
                        
    def inspecter_macro_dans_code(self):
        for index, line in enumerate(self.lines):
            strtab = line.split()
            if ((len(strtab) > 1 and strtab[0] == '#' and strtab[1].upper() == 'DEFINE')
                or (len(strtab) > 0 and strtab[0].upper() == "#DEFINE")):
                self.reporter_erreur("Presence de macros dans un fichier .c", index + 1)

    def mot_clef_dans_ligne(self, ligne):
        keyword = ["return", "while", "for", "if", "+", "-", "%"]
        strtab = ligne.split()
        for key in keyword:
            if key in strtab:
                return 1
        return 0

    def inspecter_prototype_dans_code(self):
        """ Gere pas le multiligne """
        for index, line in enumerate(self.lines):
            strtab = line.split()
            if ('=' not in line and '(' in line and ')' in line and ';' in line
                and len(strtab) > 1 and '(' in strtab[1] and self.mot_clef_dans_ligne(line) == 0
                and '(' not in strtab[0]):
                i = 0
                if line[line.index('(') + 1] == ')':
                    self.reporter_erreur("Prototype dans un fichier .c", index + 1)
                else:
                    for c in line[line.index('('):line.index(')')]:
                        if c == ' ' and i != 0:
                            self.reporter_erreur("Prototype dans un fichier .c", index + 1)
                        if c == ',':
                            i = 0
                        else:
                            i += 1

    def dans_une_chaine(self, line, index):
        chaine = False
        for i, c in enumerate(line):
            if c == '"':
                chaine = not chaine
            if i == index and chaine == True:
                return True
        return False

    def inspecter_commentaire_cpp(self):
        for index, line in enumerate(self.lines):
            found = line.find("//")
            if found >= 0 and self.dans_une_chaine(line, found) == False:
                self.reporter_erreur("Commentaire CPP", index + 1)

    def dans_une_fonction(self, index):
        fonction = False
        for i, line in enumerate(self.lines):
            if len(line) > 0 and line[0] == '{':
                fonction = True
            if len(line) > 0 and line[0] == '}':
                fonction = False
            if i == index and fonction == True:
                return True
        return False

    def inspecter_commentaire_dans_fonction(self):
        for index, line in enumerate(self.lines):
            found = line.find("/*")
            if found >= 0 and self.dans_une_chaine(line, found) == False:
                if self.dans_une_fonction(index) == True:
                    self.reporter_erreur("Commentaire dans du code", index + 1)

    def get_alignement_nom_fonction(self, line, debut):
        line = line.expandtabs(ESPACES_PAR_TABULATION)
        while debut < len(line) and line[debut] == ' ':
            debut += 1
        return debut + 1

    def is_variable_declaration(self, index):
        strtab = self.lines[index].split()
        if len(strtab) > 0 and '#' not in strtab[0]:
            if len(strtab) > 0 and strtab[0] == "static":
                return True
            elif len(strtab) == 2 and '(' not in self.lines[index]:
                return True
            elif len(strtab) == 3 and '(' not in self.lines[index] and strtab[0] == "unsigned":
                return True
        return False

    def get_alignement_variable(self, line, index):
#        print (line, end = "")
        i = 0
        while i < len(line) and (line[i] == ' ' or line[i] == '\t'):
            i += 1
        if line.find("static ", i, i + 7) != -1:
            i += 7
        if line.find("unsigned ", i, i + 9) != -1:
            i += 9
        if line.find("long long", i, i + 9) >= 0:
            i += 9
        while i < len(line) and line[i].isalnum() == True or line[i] == '_':
            i += 1
        debut = i
        while i < len(line) and (line[i] == ' ' or line[i] == '\t'):
            if line[i] == ' ':
#                print (i)
                self.reporter_erreur("Utilisation d'espace entre le type et le nom de la variable", index + 1)
                return 0
            i += 1
        alignement_variable = self.get_alignement_nom_fonction(line, debut)
#        print ("align: " + str(alignement_variable) + " line: " + str(line))
        return alignement_variable
#        print ("debut: " + str(debut) + " " + line + " " + str(alignement_variable))

    def get_alignement_nom_variable(self, index):
        alignements = []
        while index < len(self.lines) and self.lines[index][0] != '{':
            index += 1
        index += 1
        while self.is_variable_declaration(index) == True:
#            print (self.lines[index], end = "")
            alignements.append(self.get_alignement_variable(self.lines[index], index))
            index += 1
#        print (alignements)
        return alignements

    def inspecter_alignement(self):
        alignement = 0
        for index, line in enumerate(self.lines):
            if (index < len(self.lines) - 1 and len(self.lines[index + 1]) > 0
                and self.lines[index][0] != ' ' and self.lines[index][0] != '\t'
                and (self.lines[index + 1][0] == '{'
                     or (index < len(self.lines) - 2 and self.lines[index + 2][0] == '{')
                     or (index < len(self.lines) - 3 and self.lines[index + 3][0] == '{')
                     or (index < len(self.lines) - 4 and self.lines[index + 4][0] == '{'))
                and len(self.lines[index]) > 0 and self.lines[index][0] != '}'
                and self.lines[index][0] != '\n'
                and '#' not in line
                and "extern" not in line
                and line.startswith("**") == False and line.startswith("*/") == False
                and line.startswith("/*") == False
                and line.find('(') >= 0
                and '=' not in line):
                i = 0
                if line.startswith("static "):
                    i = 7
                if line.find("inline ", i, i + 7) >= 0:
                    i += 7
                if line.find("unsigned ", i, i + 9) >= 0:
                    i += 9
                if line.find("long long", i, i + 9) >= 0:
                    i += 9
                while i < len(line) and (line[i].isalnum() == True or line[i] == '_'):
                    i += 1
                debut = i
                while i < len(line) and (line[i] == ' ' or line[i] == '\t'):
                    if line[i] == ' ':
#                        print (line)
                        self.reporter_erreur("Utilisation d'espace entre le type et le nom de fonction", index + 1)
                        return 0
                    i += 1
                alignement_nom_fonction = self.get_alignement_nom_fonction(line, debut)
                alignement_nom_variable = self.get_alignement_nom_variable(index)
                if len(alignement_nom_variable) > 0:
#                    print (alignement_nom_variable)
                    for var in alignement_nom_variable:
                        if alignement_nom_fonction != var:
                            print ("var: " + str(var) + " fonction: " + str(alignement_nom_fonction))
                            return self.reporter_erreur("Mauvais alignements de la fonction avec les variables", index + 1)

    def inspecter_macro_majuscule(self):
        for index, line in enumerate(self.lines):
            if len(line) > 0:
                strtab = line.split()
                if len(strtab) > 2 and strtab[0].upper() == "#DEFINE" and strtab[1].upper() != strtab[1]:
                    self.reporter_erreur("La macro doit etre en majuscule", index + 1)
                elif (len(strtab) > 3 and strtab[0] == '#' and strtab[1].upper() == "DEFINE"
                and strtab[2].upper() != strtab[2]):
                    self.reporter_erreur("La macro doit etre en majuscule", index + 1)

    def inspecter_typedef(self):
        for index, line in enumerate(self.lines):
            strtab = line.split()
            if len(strtab) > 0 and strtab[0] == "typedef":
                if len(strtab) > 2:
                    if strtab[1] == "struct" and strtab[2].startswith("s_") == False:
                        self.reporter_erreur("Le nom de structure doit commencer par \"s_\"", index + 1)
                    elif strtab[1] == "union" and strtab[2].startswith("u_") == False:
                        self.reporter_erreur("Le nom d'union doit commencer par \"u_\"", index + 1)
                    if ';' in line and strtab[-1].startswith("t_") == False:
                        self.reporter_erreur("Le nom d'un type doit commencer par \"t_\"", index + 1)
                    elif ';' not in line:
                        i = index
                        while i < len(self.lines) and self.lines[i][0] != '}':
                            i += 1
                        if i != len(self.lines):
                            strtab2 = self.lines[i].split()
                            if len(strtab2[-1]) > 0 and strtab2[-1].startswith("t_") == False:
                                self.reporter_erreur("Le nom d'un type doit commencer par \"t_\"", index + 1)

    def inspecter_global(self):
        for index, line in enumerate(self.lines):
            strtab = line.split()
            if (len(strtab) > 1 and self.dans_une_fonction(index) == False
                and line.startswith("**") == False and line.startswith("/*") == False
                and line.startswith("*/") == False and '#' not in line
                and '(' not in line and ')' not in line):
                if (len(strtab) > 3 and strtab[-1] == '{' and strtab[-2] == '='
                    and strtab[-3].startswith("g_") == False):
                    self.reporter_erreur("1Une globale doit commencer \"g_\"", index + 1)
                elif (len(strtab) > 2 and strtab[-1] == '=' and strtab[-2].startswith("g_") == False):
                    self.reporter_erreur("2Une globale doit commencer \"g_\"", index + 1)
                elif strtab[1].startswith("g_") == False and strtab[1][-1] == ';' and strtab[0] != '}':
                    self.reporter_erreur("3Une globale doit commencer \"g_\"", index + 1)

    def inspecter_h(self):
        self.inspecter_macro_temoin()
        self.inspecter_fonctions_dans_header()

    def inspecter_c(self):
        self.inspecter_macro_dans_code()
        self.inspecter_prototype_dans_code()
        self.inspecter_alignement()

    def inspecter_fichier(self):
        try:
            self.f = open(self.nom_fichier, "r")
        except:
            print ("Impossible d'ouvrir " + self.nom_fichier)

        for line in self.f:
            self.lines.append(line)
        self.f.close()
        self.nb_lignes = len(self.lines)

#        print (file)
        if self.nom_fichier.endswith(".h"):
            self.inspecter_h()
        else:
            self.inspecter_c()
        self.inspecter_entete()
        self.inspecter_nombre_colonnes()
        self.inspecter_nombre_instruction()
        self.inspecter_nombre_ligne_par_fonction()
        self.inspecter_nombre_fonctions()
        self.inspecter_macro_multilignes()
        self.inspecter_commentaire_cpp()
        self.inspecter_commentaire_dans_fonction()
        self.inspecter_macro_majuscule()
        self.inspecter_typedef()
        self.inspecter_global()
        
def get_list_files(dir_name):
    files = []
    for path, dirs, filenames in os.walk(dir_name):
        for file in filenames:
            if file.endswith(".h") or file.endswith(".c"):
                files.append(os.path.join(path, file))
    return files

def afficher_erreur(nb):
    if nb == 0:
        print (Fore.GREEN + "Aucune erreur trouve" + Fore.RESET)
    else:
        print("")
        print (Fore.YELLOW + str(nb) + " erreurs et dangers trouves" + Fore.RESET)

def afficher_logins():
    if len(auteurs) > 0:
        print ("Logins trouves: " + Fore.GREEN + " ".join(auteurs) + Fore.RESET)
    else:
        print ("Aucun login trouve")
        
if __name__ == '__main__':
    if len(sys.argv) <= 1:
        print ("Usage: ./" + sys.argv[0] + " __DIRECTORY__")
    else:
        if platform.system() == "Windows":
            init()
        files = get_list_files(sys.argv[1])
        nb_erreurs = 0
        for file in files:
            check = Norme(file)
            check.inspecter_fichier()
            check.afficher_dangers()
            check.afficher_erreurs()
            nb_erreurs += check.nombres_erreurs_et_dangers()
        afficher_erreur(nb_erreurs)
        afficher_logins()
