import os
import json

def save_viral_segments(segments_data=None, project_folder="tmp"):
    output_txt_file = os.path.join(project_folder, "viral_segments.txt")

    # Verifica se os arquivos já existem
    if not os.path.exists(output_txt_file):
        if segments_data is None:
            # Solicita ao usuário que insira o JSON caso o arquivo não exista e os segmentos não estejam definidos
            while True:
                user_input = input("\nSilakan masukkan JSON segmen dalam format yang sesuai:\n")
                try:
                    # Tenta carregar o JSON inserido
                    segments_data = json.loads(user_input)

                    # Valida se o formato está correto
                    if "segments" in segments_data and isinstance(segments_data["segments"], list):
                        # Salva os dados em um arquivo JSON
                        with open(output_txt_file, 'w', encoding='utf-8') as file:
                            json.dump(segments_data, file, ensure_ascii=False, indent=4)
                        print(f"Segmen viral berhasil disimpan di: {output_txt_file}")
                        break
                    else:
                        print("Format tidak valid. Pastikan struktur JSON berisi 'segments'.")
                except json.JSONDecodeError:
                    print("Error membaca JSON. Periksa kembali format teks JSON Anda.")
                print("Silakan coba lagi.")
        else:
            # Caso os segmentos tenham sido gerados, salva automaticamente
            with open(output_txt_file, 'w', encoding='utf-8') as file:
                json.dump(segments_data, file, ensure_ascii=False, indent=4)
            print(f"Segmen viral disimpan di: {output_txt_file}\n")
    else:
        print(f"File {output_txt_file} sudah ada. Menggunakan data yang ada.")