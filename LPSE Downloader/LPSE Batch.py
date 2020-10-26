from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from os import system
import sys, time, datetime, csv, pandas as pd

#Hide Traceback
sys.tracebacklimit = 0

#berapa lama selesai?
app_start = datetime.datetime.now()

def clear_line():
    sys.stdout.write("\033[F") #back to previous line
    sys.stdout.write("\033[K") #clear line

def banner():
    print('''
         ___
     ___/   \\  _    ___  ___ ___   ___   _ _____ ___ _  _   ___                  _              _         
    /   \\___/ | |  | _ \\/ __| __| | _ ) / \\_   _/ __| || | |   \\ _____ __ ___ _ | |___  __ _ __| |___ _ _ 
    \\___/   \\ | |__|  _/\\__ \\ _|  | _ \\/ _ \\| |\\ (__| __ | | |) / _ \\ V  V / ' \\| / _ \\/ _` / _` / -_) '_|
        \\___/ |____|_|  |___/___| |___/_/ \\_\\_| \\___|_||_| |___/\\___/\\_/\\_/|_||_|_\\___/\\__,_\\__,_\\___|_|
          v.1.86.0 by @seimpairiyun
    ''')

#set title window
title = "LPSE Batch Downloader"
system("cls")
system("title "+title)

options = Options()
options.add_argument("--headless")
options.add_argument("--log-level=3")

driver = webdriver.Chrome("/LPSE Downloader/chromedriver.exe",options=options)

def lpse_batch(link_lpse, tahun):
    #Variable link_dalam_csv sbg Keyword link_lpse
    link_dalam_csv = link_lpse
    link_target = link_dalam_csv +"/eproc4/lelang"
    try:
        #Cek link LPSE
        Link = link_target
        CekLink = Link.find('lpse')

        if CekLink == 7 or CekLink == 8:
            #Durasi download
            download_start = datetime.datetime.now()

            driver.get(link_target)
            #jumlah data LPSE
            try:
                WebDriverWait(driver, 10).until(
                        expected_conditions.presence_of_element_located((By.CLASS_NAME, "dataTables_info"))
                        )
                dataTables_info = driver.find_element_by_class_name("dataTables_info")
            except:
                pass

            #info LPSE
            info_lpse = dataTables_info.text
            filter_dari = info_lpse.find("dari")
            JumlahData = info_lpse[filter_dari+5:None].replace(',','').replace(' data','')
            JumlahData_string = info_lpse[filter_dari+5:None].replace(' data','')

            link = driver.current_url
            x = link.find("/l")
            y = link.find(".go.")
            namafile = link[x+1:y]
            target = link[0:y]

            #Ubah Option halaman jadi lebih banyak 
            page = driver.find_element_by_name("tbllelang_length")
            driver.execute_script("arguments[0].innerHTML = '<option value=1>114</option><option value="+ JumlahData +">get</option>';", page)
            driver.find_element_by_xpath("//select[@name='tbllelang_length']/option[text()='get']").click()

            #jeda agar halaman terload semua
            def delay_halaman(JumlahData_string):
                try:
                    text = 'Tampilan 1 sampai ' + JumlahData_string
                    WebDriverWait(driver, 90).until(
                        expected_conditions.presence_of_element_located((By.XPATH, "//div[@class='dataTables_info' and contains(text(),'"+text+"')]"))
                        )
                    driver.find_element_by_class_name("dataTables_info")
                except:
                    print(link_dalam_csv)
                    print(' ==> '+'\x1b[0;33;40m'+'Data susah ditarik karena website lambat..'+'\x1b[0m\n')
                    pass

            delay_halaman(JumlahData_string)

            #Grap semua data di Tabel Lelang 
            tabelLelang = driver.find_element_by_xpath("//table[@id='tbllelang']").text
            table_text = tabelLelang.split('-')

            #Variable InputTahun sbg Keyword tahun
            InputTahun = tahun

            try:
                TahunAnggaran = int(InputTahun) - 1 
                TA = ' TA '+ str(TahunAnggaran) +' '

                #Convert Tabel_text jadi Dataframe
                df = pd.DataFrame (table_text,columns=['Tahun_Anggaran'])
                #Filter Hanya Text yg mengandung kata '% TA %' 
                list_tahun = df[df['Tahun_Anggaran'].str.contains(" TA ")].reset_index()

                #Cari Baris keberapa Tahun yg diinput
                cari_tahun = list_tahun['Tahun_Anggaran'].loc[lambda x: x == TA].index
                #Jumlah baris yang akan ditarik
                JumlahLPSE = int(cari_tahun[1]) - 1
                
                #Cek Filter bener gk hanya mengandung kata '% TA %'
                #print(list_tahun['Tahun_Anggaran'].tolist())
            except:
                print(link_dalam_csv)
                print(' ==> ','\x1b[1;33;40m'+'Tahun Anggaran tidak ditemukan..'+'\x1b[0m')
                print()
                #driver.close()
                #driver.quit()
                pass       

            #Setelah fixed TA, tarik ulang kode tender sebanyak baris TA
            #Ubah Option halaman jadi lebih banyak 
            driver.refresh()
            page = driver.find_element_by_name("tbllelang_length")
            driver.execute_script("arguments[0].innerHTML = '<option value=1>114</option><option value="+str(JumlahLPSE)+">get</option>';", page)
            driver.find_element_by_xpath("//select[@name='tbllelang_length']/option[text()='get']").click()

            #jeda agar halaman terload semua
            JumlahData_string = str(JumlahLPSE)
            delay_halaman(JumlahData_string)

            #proses download kode tender
            lelangs = driver.find_elements_by_xpath("//td[@class='sorting_1']")

            line_tender = 0
            kode = []
            for lelang in lelangs:
                link1 = target+".go.id/eproc4/lelang/"+lelang.text+"/pengumumanlelang"
                link2 = target+".go.id/eproc4/evaluasi/"+lelang.text+"/pemenang"

                #satuin kode tender
                kode.append((link1,link2))

                #info
                line_tender += 1 
                
            #export to data.csv
            df = pd.DataFrame(kode, columns=['link_pengumuman','link_pemenang'])
            df.to_csv('data.csv', index=False, encoding='utf-8')

            #proses web scrapping sesuai link.csv
            data_lpse = []
            line_tender = 0
            with open("data.csv", "r") as csv_file:
                csv_reader = csv.DictReader(csv_file, delimiter=',')
                for lines in csv_reader:
                    #auto number
                    line_tender += 1

                    ##buka link pengumuman##
                    driver.get(lines['link_pengumuman'])
                    #time.sleep(0.5)
                    
                    #Link Tender
                    LinkTender = lines['link_pengumuman']
                    print(link_dalam_csv)
                    print(' ==> ' + '\x1b[1;37;7m' + ' ' + str(JumlahLPSE)+' data lelang ditemukan.'+'\x1b[0m' + ' Status: Downloading ['+str(line_tender)+'/'+str(JumlahLPSE)+']')
                    clear_line()
                    clear_line()

                    #Nama Tender
                    time.sleep(0.1)
                    NamaTender = driver.find_element_by_xpath("//table[@class='table table-condensed table-bordered']/tbody/tr[2]/td/strong").get_attribute("innerHTML")

                    #Tanggal Pembuatan
                    time.sleep(0.1)
                    TglPembuatan = driver.find_element_by_xpath("//table[@class='table table-condensed table-bordered']/tbody/tr[4]/td").get_attribute("innerHTML")

                    #Tahap Tender
                    time.sleep(0.1)
                    try:
                        Tahap = driver.find_element_by_xpath("//table[@class='table table-condensed table-bordered']/tbody/tr[6]/td/a").get_attribute("innerHTML").replace("[...]","")
                    except:
                        Tahap = driver.find_element_by_xpath("//table[@class='table table-condensed table-bordered']/tbody/tr[7]/td/a").get_attribute("innerHTML").replace("[...]","")

                    #Instansi
                    time.sleep(0.1)
                    Instansi_ = driver.find_element_by_xpath("//table[@class='table table-condensed table-bordered']/tbody/tr[7]/td").get_attribute("innerHTML")
                    if Instansi_[0:2]=='<a':
                        Instansi = driver.find_element_by_xpath("//table[@class='table table-condensed table-bordered']/tbody/tr[8]/td").get_attribute("innerHTML").strip()
                    else:
                        Instansi = driver.find_element_by_xpath("//table[@class='table table-condensed table-bordered']/tbody/tr[7]/td").get_attribute("innerHTML").strip()

                    #Satker
                    time.sleep(0.1)
                    if Instansi_[0:2]=='<a':
                        Satker = driver.find_element_by_xpath("//table[@class='table table-condensed table-bordered']/tbody/tr[9]/td").get_attribute("innerHTML")
                    else:
                        Satker = driver.find_element_by_xpath("//table[@class='table table-condensed table-bordered']/tbody/tr[8]/td").get_attribute("innerHTML")

                    #Kategori
                    time.sleep(0.1)
                    if Instansi_[0:2]=='<a':
                        Kategori = driver.find_element_by_xpath("//table[@class='table table-condensed table-bordered']/tbody/tr[10]/td").get_attribute("innerHTML").strip()
                    else:
                        Kategori = driver.find_element_by_xpath("//table[@class='table table-condensed table-bordered']/tbody/tr[9]/td").get_attribute("innerHTML").strip()

                    #Tahun Anggaran
                    time.sleep(0.1)
                    if Instansi_[0:2]=='<a':
                        TahunAnggaran = driver.find_element_by_xpath("//table[@class='table table-condensed table-bordered']/tbody/tr[12]/td").get_attribute("innerHTML").replace("&nbsp;", "").strip()
                    else:
                        TahunAnggaran = driver.find_element_by_xpath("//table[@class='table table-condensed table-bordered']/tbody/tr[11]/td").get_attribute("innerHTML").replace("&nbsp;", "").strip()

                    #Nilai PAGU
                    time.sleep(0.1)
                    if Instansi_[0:2]=='<a':
                        PAGU = float(driver.find_element_by_xpath("//table[@class='table table-condensed table-bordered']/tbody/tr[13]/td[1]").get_attribute("innerHTML").replace("Rp ","").replace(",00","").replace(".","").replace(",","."))
                    else:
                        PAGU = float(driver.find_element_by_xpath("//table[@class='table table-condensed table-bordered']/tbody/tr[12]/td[1]").get_attribute("innerHTML").replace("Rp ","").replace(",00","").replace(".","").replace(",","."))

                    #Nilai HPS
                    time.sleep(0.1)
                    if Instansi_[0:2]=='<a':
                        HPS = float(driver.find_element_by_xpath("//table[@class='table table-condensed table-bordered']/tbody/tr[13]/td[2]").get_attribute("innerHTML").replace("Rp ","").replace(",00","").replace(".","").replace(",","."))
                    else:
                        HPS = float(driver.find_element_by_xpath("//table[@class='table table-condensed table-bordered']/tbody/tr[12]/td[2]").get_attribute("innerHTML").replace("Rp ","").replace(",00","").replace(".","").replace(",","."))

                    #Klasifikasi
                    time.sleep(0.1)
                    if Instansi_[0:2]=='<a':
                        Klasifikasi = driver.find_element_by_xpath("//table[@class='table table-condensed table-bordered']/tbody/tr[16]/td").get_attribute("innerHTML")
                    else:
                        if Klasifikasi[0:2]=='<t':
                            Klasifikasi = '-'            
                        Klasifikasi = driver.find_element_by_xpath("//table[@class='table table-condensed table-bordered']/tbody/tr[15]/td").get_attribute("innerHTML")

                    ## buka link pemenang ##
                    driver.get(lines['link_pemenang'])

                    #Nama Pemenang
                    try:
                        Pemenang = driver.find_element_by_xpath("//table[@class='table table-condensed']/tbody/tr[7]/td/table[@class='table table-condensed']/tbody/tr[2]/td[1]").get_attribute("innerHTML")
                    except:	
                        Pemenang = "-"

                    #Alamat	Pemenang
                    try:
                        Alamat = driver.find_element_by_xpath("//table[@class='table table-condensed']/tbody/tr[7]/td/table[@class='table table-condensed']/tbody/tr[2]/td[2]").get_attribute("innerHTML").replace('<strong>','').replace('</strong>','')
                    except:
                        Alamat = "-"

                    #NPWP
                    try:	
                        NPWP = driver.find_element_by_xpath("//table[@class='table table-condensed']/tbody/tr[7]/td/table[@class='table table-condensed']/tbody/tr[2]/td[3]").get_attribute("innerHTML").replace(".","")
                    except:
                        NPWP = "-"

                    #Harga Penawaran
                    try:		
                        Penawaran = float(driver.find_element_by_xpath("//table[@class='table table-condensed']/tbody/tr[7]/td/table[@class='table table-condensed']/tbody/tr[2]/td[4]").get_attribute("innerHTML").replace("Rp ","").replace(",00","").replace(".","").replace(",","."))
                    except:
                        Penawaran = "-"

                    #Harga Terkoreksi
                    try:	
                        Terkoreksi = float(driver.find_element_by_xpath("//table[@class='table table-condensed']/tbody/tr[7]/td/table[@class='table table-condensed']/tbody/tr[2]/td[5]").get_attribute("innerHTML").replace("Rp ","").replace(",00","").replace(".","").replace(",","."))
                    except:
                        Terkoreksi = "-"

                    #Hasil Negosiasi		
                    try:
                        Negosiasi = float(driver.find_element_by_xpath("//table[@class='table table-condensed']/tbody/tr[7]/td/table[@class='table table-condensed']/tbody/tr[2]/td[6]").get_attribute("innerHTML").replace("Rp ","").replace(",00","").replace(".","").replace(",","."))
                    except:
                        Negosiasi = "-"

                    #satuin data untuk di export ke csv
                    data_lpse.append((LinkTender,NamaTender,TglPembuatan,Tahap,Instansi,Satker,Kategori,TahunAnggaran,PAGU,HPS,Klasifikasi,Pemenang,Alamat,NPWP,Penawaran,Terkoreksi,Negosiasi))

            #export data lpse ke csv 
            df = pd.DataFrame(data_lpse, columns=["link","Nama_Tender","Tgl_Pembuatan","Tahap","Instansi","Satker","Kategori","Tahun_Anggaran","Nilai_PAGU","Nilai_HPS","Klasifikasi","Pemenang","Alamat","NPWP","Harga_Penawaran","Harga_Terkoreksi","Hasil_Negosiasi"])
            df.to_csv('download/batch_'+namafile+'.csv', index=False, encoding='utf-8')

            #berapa lama selesai??
            download_stop = datetime.datetime.now()
            selisih_waktu_download = download_stop - download_start
            durasi_download = divmod(selisih_waktu_download.seconds, 60)

            #selesai
            print(link_dalam_csv)
            print('\x1b[1;33;40m' + ' ==> ' + '\x1b[0m' + '\x1b[1;37;7m' + ' ' + str(JumlahLPSE) + ' data lelang tersimpan.' + '\x1b[0m' + ' Status: ' + '\x1b[1;32;7m' + ' Selesai ' + '\x1b[0m' + ' [Waktu Download:', durasi_download[0], 'menit', durasi_download[1], 'detik]')
            print()
        elif CekLink != 7 or CekLink != 8:
            print(link_dalam_csv)
            print(' ==> '+'\x1b[0;31;40m'+'Link tidak sesuai!'+'\x1b[0m\n')
            pass
    except KeyboardInterrupt:
        print(link_dalam_csv)
        print(' ==> '+'\x1b[0;31;40m'+'Proses scrapping dibatalkan.'+'\x1b[0m\n')
        sys.exit()
        driver.close()
        driver.quit()
    except:
        print(link_dalam_csv)
        print(' ==> '+'\x1b[0;31;40m'+'Link gagal diakses!'+'\x1b[0m\n')
        pass


########################################################################################################

#welcome
system("cls")
banner()
print()
print("Masukkan link LPSE dengan benar ke dalam file link_batch.csv (perhatikan http atau https).")
print("\x1b[1;34;40m"+"Contoh:"+"\x1b[0m"+" http://lpse.bireuenkab.go.id atau https://lpse.tebingtinggikota.go.id")
print("Pastikan internet stabil, cepat dan tidak lambat.")
print()

#input tahun anggaran
while True:
    tahun = input("\x1b[1;33;40m"+"Tarik data lelang dari Tahun ==> "+"\x1b[0m")

    if len(tahun) != 4 or tahun[0:2] != '20' or tahun == str():
        print('Tahun tidak benar')
        clear_line()
        clear_line()
    else:
        break

print()

jumlah_link = 0
with open("link_batch.csv", "r") as csv_file:
        csv_batch_reader = csv.DictReader(csv_file, delimiter=',')
        for linkLPSE in csv_batch_reader:
            jumlah_link += 1
            print('Tunggu sebentar, load', jumlah_link, 'link LPSE')
            clear_line()
            time.sleep(0.1)

#proses download lpse batch
with open("link_batch.csv", "r") as csv_file:
        csv_batch_reader = csv.DictReader(csv_file, delimiter=',')
        for linkLPSE in csv_batch_reader:

            link_dalam_csv = linkLPSE['link_batch']
            lpse_batch(link_dalam_csv, tahun)

#berapa lama selesai??
app_stop = datetime.datetime.now()
selisih = app_stop - app_start
durasi = divmod(selisih.seconds, 60)

print('Scrapping dari', jumlah_link, 'link LPSE.' + ' [Durasi:', durasi[0], 'menit', durasi[1], 'detik]\n')

#tutup koneksi driver
driver.close()

