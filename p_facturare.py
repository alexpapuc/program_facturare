from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Float,
    Date,
    ForeignKey,
    Table,
)
from sqlalchemy.orm import relationship, sessionmaker, declarative_base
from sqlalchemy.ext.declarative import declared_attr
from datetime import datetime
from mailmerge import MailMerge


flag_program = True
# cream engine pentru conectarea la baza de date
engine = create_engine("sqlite:///db_facturare.db")
print(engine.connect())

Base = declarative_base()

# Many to Many tabel de relatie pentru Factura-Produs
factura_produs_association = Table(
    "factura_produs",
    Base.metadata,
    Column("factura_id", Integer, ForeignKey("facturi.id")),
    Column("produs_id", Integer, ForeignKey("produse.id")),
)


class Furnizor(Base):
    __tablename__ = "furnizori"
    id = Column(Integer, primary_key=True)
    denumire = Column(String(50), nullable=False)
    cif = Column(String(20), nullable=False)
    adresa = Column(String(100), nullable=False)
    facturi = relationship("Factura", back_populates="furnizor")

    def __repr__(self):
        return f"Furnizor(id={self.id}, denumire={self.denumire}, cif={self.cif}, adresa={self.adresa})"


class Client(Base):
    __tablename__ = "clienti"
    id = Column(Integer, primary_key=True)
    denumire = Column(String(50), nullable=False)
    cif = Column(String(20), nullable=False)
    adresa = Column(String(100), nullable=False)
    facturi = relationship("Factura", back_populates="client")

    def __repr__(self):
        return f"Client(id={self.id}, denumire={self.denumire}, cif={self.cif}, adresa={self.adresa})"


class Produs(Base):
    __tablename__ = "produse"
    id = Column(Integer, primary_key=True)
    denumire = Column(String(50), nullable=False)
    cantitate = Column(Integer, nullable=False)
    pret_unitar = Column(Float, nullable=False)
    facturi = relationship(
        "Factura", secondary=factura_produs_association, back_populates="produse"
    )

    def __repr__(self):
        return f"Produs(id={self.id}, denumire={self.denumire}, cantitate={self.cantitate}, pret_unitar={self.pret_unitar})"


class Factura(Base):
    __tablename__ = "facturi"
    id = Column(Integer, primary_key=True)
    data_emitere = Column(Date, default=datetime.now())
    furnizor_id = Column(Integer, ForeignKey("furnizori.id"))
    client_id = Column(Integer, ForeignKey("clienti.id"))
    furnizor = relationship("Furnizor", back_populates="facturi")
    client = relationship("Client", back_populates="facturi")
    produse = relationship(
        "Produs", secondary=factura_produs_association, back_populates="facturi"
    )

    def pret_total_per_articol(self, tva=0.19):
        # print(self.produse)
        return [
            (
                produs.denumire,
                produs.cantitate,
                produs.pret_unitar,
                round(produs.cantitate * produs.pret_unitar, 2),
                round(produs.cantitate * produs.pret_unitar * tva, 2),
            )
            for produs in self.produse
        ]

    def calculare_total_fara_tva(self):
        return round(
            sum(
                round(produs.pret_unitar * produs.cantitate, 2)
                for produs in self.produse
            ),
            2,
        )

    def calculare_subtotal_tva(self, tva=0.19):
        return round(
            sum(
                round(produs.cantitate * produs.pret_unitar * tva, 2)
                for produs in self.produse
            ),
            2,
        )

    def calculare_total_cu_tva(self, tva=0.19):
        return round(self.calculare_total_fara_tva() * (1 + tva), 2)

    def __repr__(self):
        return f"Factura(id={self.id}, data_emitere={self.data_emitere}, furnizor_id={self.furnizor_id}, client_id={self.client_id})"


# Creaza sesiunea de comunicare cu baza de date
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()

# Metode pentru adaugare, afisare, stergere furnizori, clienti, produse, facturi


def adauga_furnizor(denumire, cif, adresa):
    furnizor = Furnizor(denumire=denumire, cif=cif, adresa=adresa)
    session.add(furnizor)
    session.commit()
    return furnizor


def afiseaza_furnizori():
    return session.query(Furnizor).all()


def sterge_furnizor(furnizor_id):
    furnizor = session.query(Furnizor).filter_by(id=furnizor_id).first()
    if furnizor:
        print(f"Am gasit furnizorul: {furnizor}")
        session.delete(furnizor)
        session.commit()
        print(f"Furnizorul cu ID-ul {furnizor_id} a fost sters.")
    else:
        print(f"Furnizorul cu ID-ul {furnizor_id} nu a fost gasit in baza de date.")


def adauga_client(denumire, cif, adresa):
    client = Client(denumire=denumire, cif=cif, adresa=adresa)
    session.add(client)
    session.commit()
    return client


def afiseaza_clienti():
    return session.query(Client).all()


def sterge_client(client_id):
    client = session.query(Client).filter_by(id=client_id).first()
    if client:
        print(f"Am gasit clientul: {client}")
        session.delete(client)
        session.commit()
        print(f"Clientul cu ID-ul {client_id} a fost sters.")
    else:
        print(f"Clientul cu ID-ul {client_id} nu a fost gasit in baza de date.")


def adauga_produs(denumire, cantitate, pret_unitar):
    produs = Produs(denumire=denumire, cantitate=cantitate, pret_unitar=pret_unitar)
    session.add(produs)
    session.commit()
    return produs


def afiseaza_produse():
    return session.query(Produs).all()


def sterge_produs(produs_id):
    produs = session.query(Produs).filter_by(id=produs_id).first()
    if produs:
        print(f"Produsul gasit: {produs}")
        session.delete(produs)
        session.commit()
        print(f"Produsul cu ID-ul {produs_id} a fost sters.")
    else:
        print(f"Produsul cu ID-ul {produs_id} nu a fost gasit in baza de date.")


def emite_factura(furnizor_id, client_id, produse_ids):
    # verificam daca furnizorul este in baza de date
    furnizor = session.query(Furnizor).filter_by(id=furnizor_id).first()
    if not furnizor:
        print(f"Furnizorul cu ID-ul {furnizor_id} nu a fost gasit in baza de date.")
        return None

    # verificam daca clientul exista in baza de date
    client = session.query(Client).filter_by(id=client_id).first()
    if not client:
        print(f"Clientul cu ID-ul {client_id} nu a fost gasit in baza de date.")
        return None

    # Verificam daca toate produsele exista in baza de date
    produse = session.query(Produs).filter(Produs.id.in_(produse_ids)).all()
    if len(produse) != len(produse_ids):
        produse_gasite_ids = {produs.id for produs in produse}
        produse_lipsa_ids = set(produse_ids) - produse_gasite_ids
        print(
            f"Produsele cu urmatoarele ID-uri nu au fost gasite in baza de date: {', '.join(map(str, produse_lipsa_ids))}"
        )
        return None

    # Dacă toate verificările sunt trecute, emite factura
    factura = Factura(furnizor_id=furnizor_id, client_id=client_id, produse=produse)
    session.add(factura)
    session.commit()
    print(f"Factura a fost emisă cu succes. ID-ul facturii este: {factura.id}")
    return factura


def sterge_factura(factura_id):
    factura = session.query(Factura).filter_by(id=factura_id).first()
    if factura:
        print(f"Factura gasita: {factura}")
        session.delete(factura)
        session.commit()
        print(f"Factura cu ID-ul {factura_id} a fost ștearsa.")
    else:
        print(f"Factura cu ID-ul {factura_id} nu a fost gasita in baza de date.")


def transformare_string(produse):
    for produs in produse:
        for k, v in produs.items():
            produs[k] = str(v)
    return produse


def exporta_factura(factura, produse):
    """
    exporta_factura(): va scrie intr - un fisier text, intr - un format frumos, toate
    detaliile facturii: client, furnizor, produse, preturi
    :return:
    """
    template = "template_factura.docx"
    document = MailMerge(template)
    # print(document.get_merge_fields())

    document.merge(
        nr_factura=str(factura.id),
        data=str(factura.data_emitere),
        den_furnizor=str(factura.furnizor.denumire),
        cui_furnizor=str(factura.furnizor.cif),
        adresa_furnizor=str(factura.furnizor.adresa),
        den_client=str(factura.client.denumire),
        cui_client=str(factura.client.cif),
        adresa_client=str(factura.client.adresa),
        subtotal_fara_tva=str(factura.calculare_total_fara_tva()),
        subtotal_tva=str(factura.calculare_subtotal_tva()),
        total_facturat=str(factura.calculare_total_cu_tva()),
    )

    # transformam toate valorile dictionarelor in string ca sa poata fi scrise in word
    produse_str = transformare_string(produse)

    # scriem produsele in word
    document.merge_rows("nr_crt", produse_str)
    document.write(f"factura{factura.id}.docx")


def exit():
    flag_program = False
    return flag_program


while flag_program is True:

    alegere = input(
        """Introdu cifra corespunzatoare operatiunii dorite: 
    1 Afisare furnizori, clienti, produse, facturi; 
    2 Adaugare furnizori, clienti, produse, Emitere facturi;
    3 Stergere furnizori, clienti, produse, facturi
    0 Exit"""
    )

    try:
        if int(alegere) == 1:
            flag_afisare = True
            while flag_afisare is True:
                optiune_afisare = input(
                    """Introdu cifra corespunzatoare operatiunii dorite: 
                            1 Afisare furnizori; 
                            2 Afisare clienti; 
                            3 Afisare produse;
                            4 Afisare facturi emise
                            0 Intoarcere la pasul anterior"""
                )
                try:
                    if int(optiune_afisare) == 1:
                        print(session.query(Furnizor).all())
                    elif int(optiune_afisare) == 2:
                        print(session.query(Client).all())
                    elif int(optiune_afisare) == 3:
                        print(session.query(Produs).all())
                    elif int(optiune_afisare) == 4:
                        print(session.query(Factura).all())
                    elif int(optiune_afisare) == 0:
                        flag_afisare = False
                except ValueError:
                    print(
                        "Nu ai introdus o optiune valida! Introdu una din optiunile afisate in terminal!"
                    )

        elif int(alegere) == 2:
            flag_adaugare = True
            while flag_adaugare is True:
                optiune_adaugare = input(
                    """Introdu cifra corespunzatoare operatiunii dorite: 
                                        1 Adauga furnizori; 
                                        2 Adauga clienti; 
                                        3 Adauga produse;
                                        4 Emite facturi
                                        0 Intoarcere la pasul anterior"""
                )
                try:
                    if int(optiune_adaugare) == 1:
                        print(
                            "Introdu datele sub forma: Denumire Furnizor, RO123456, Adresa furnizor"
                        )
                        date_furnizor = input("Introdu datele despre noul furnizor: ")
                        # despachetam datele si eliminam spatiile care pot aparea
                        furnizor = [item.strip() for item in date_furnizor.split(",")]
                        # adaugam furnizorul in baza de date
                        # furnizor = adauga_furnizor('Denumire Furnizor', 'RO123456', 'Adresa furnizor')
                        adauga_furnizor(furnizor[0], furnizor[1], furnizor[2])

                    elif int(optiune_adaugare) == 2:
                        print(
                            "Introdu datele sub forma: Denumire Client, RO123456, Adresa client"
                        )
                        date_client = input("Introdu datele despre noul client: ")
                        # despachetam datele si eliminam spatiile care pot aparea
                        client = [item.strip() for item in date_client.split(",")]
                        # adaugam clientul in baza de date
                        # furnizor = adauga_furnizor('Denumire Furnizor', 'RO123456', 'Adresa furnizor')
                        adauga_client(client[0], client[1], client[2])

                    elif int(optiune_adaugare) == 3:
                        print(
                            "Introdu datele sub forma: Denumire produs, cantitate, pret unitar"
                        )
                        date_produs = input("Introdu datele despre noul produs: ")
                        # despachetam datele si eliminam spatiile care pot aparea
                        produs = [item.strip() for item in date_produs.split(",")]
                        # adauga_produs('Produs 1', 10, 5.0)
                        # adaugam produsul in baza de date
                        adauga_produs(produs[0], int(produs[1]), float(produs[2]))

                    elif int(optiune_adaugare) == 4:
                        try:
                            print(session.query(Furnizor).all())
                            print(session.query(Client).all())
                            print(session.query(Produs).all())
                            print(
                                "Introdu datele sub forma: id furnizor, id client, produs1, produs2, ...., produs_n"
                            )
                            date_factura = input("Introdu datele despre factura: ")
                            info_pt_factura = [
                                item.strip() for item in date_factura.split(",")
                            ]
                            # factura = emite_factura(3, 3, [3, 4, 5])
                            prod_pt_factura = info_pt_factura[2:]
                            # transform elementele listei din str in integer
                            prod_pt_factura = [
                                int(prod_pt_factura[i])
                                for i in range(len(prod_pt_factura))
                            ]
                            factura = emite_factura(
                                int(info_pt_factura[0]),
                                int(info_pt_factura[1]),
                                prod_pt_factura,
                            )
                            # factura.exporta_factura()
                            # obtin o lista de tupluri(produse) de forma
                            # [('Produs 1', 10, 5.0, 50.0, 9.5), ('Produs 2', 20, 2.5, 50.0, 9.5)]
                            produse_db = factura.pret_total_per_articol()
                            produse = []
                            for i in range(len(produse_db)):
                                produs = {}
                                produs["nr_crt"] = i + 1
                                produs["descriere"] = produse_db[i][0]
                                produs["unitate"] = "BUC"
                                produs["cantitate"] = produse_db[i][1]
                                produs["pret_unitar"] = produse_db[i][2]
                                produs["pret_total"] = produse_db[i][3]
                                produs["tva"] = produse_db[i][4]
                                produse.append(produs)
                            # print(produse)
                            exporta_factura(factura, produse)
                        except AttributeError:
                            print(
                                "Verifica datele introduse, un id introdus nu se afla in baza de date! Reincearca!"
                            )
                        except IndexError:
                            print(
                                "Nu ai introdus datele similar formatului din exemplu! Reincearca!"
                            )

                    elif int(optiune_adaugare) == 0:
                        flag_adaugare = False
                except ValueError:
                    print(
                        "Nu ai introdus o optiune valida! Introdu una din optiunile afisate in terminal!"
                    )

        elif int(alegere) == 3:
            flag_stergere = True
            while flag_stergere is True:
                optiune_stergere = input(
                    """Introdu cifra corespunzatoare operatiunii dorite: 
                                                    1 Sterge furnizori; 
                                                    2 Sterge clienti; 
                                                    3 Sterge produse;
                                                    4 Sterge facturi
                                                    0 Intoarcere la pasul anterior"""
                )
                try:
                    if int(optiune_stergere) == 1:
                        try:
                            print(session.query(Furnizor).all())
                            furnizor_id = input(
                                "Introdu id-ul furnizorului pe care vrei sa il stergi: "
                            )
                            sterge_furnizor(int(furnizor_id))
                        except ValueError:
                            print(
                                "Nu ai introdus o optiune valida! Introdu unul din ID-urile afisate in terminal!"
                            )
                    elif int(optiune_stergere) == 2:
                        try:
                            print(session.query(Client).all())
                            client_id = input(
                                "Introdu id-ul clientului pe care vrei sa il stergi: "
                            )
                            sterge_client(int(client_id))
                        except ValueError:
                            print(
                                "Nu ai introdus o optiune valida! Introdu unul din ID-urile afisate in terminal!"
                            )
                    elif int(optiune_stergere) == 3:
                        try:
                            print(session.query(Produs).all())
                            produs_id = input(
                                "Introdu id-ul produsului pe care vrei sa il stergi: "
                            )
                            sterge_produs(int(produs_id))
                        except ValueError:
                            print(
                                "Nu ai introdus o optiune valida! Introdu unul din ID-urile afisate in terminal!"
                            )
                    elif int(optiune_stergere) == 4:
                        try:
                            print(session.query(Factura).all())
                            factura_id = input(
                                "Introdu id-ul facturii pe care vrei sa o stergi: "
                            )
                            sterge_factura(int(factura_id))
                        except ValueError:
                            print(
                                "Nu ai introdus o optiune valida! Introdu unul din ID-urile afisate in terminal!"
                            )
                    elif int(optiune_stergere) == 0:
                        flag_stergere = False
                except ValueError:
                    print(
                        "Nu ai introdus o optiune valida! Introdu una din optiunile afisate in terminal!"
                    )

        elif int(alegere) == 0:
            flag_program = exit()
    except ValueError:
        print(
            "Nu ai introdus o optiune valida! Introdu una din optiunile afisate in terminal!"
        )
