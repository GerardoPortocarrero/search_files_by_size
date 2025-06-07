import os
from tqdm import tqdm
import pandas as pd

def gestionar_csv_cambios(df_nueva_ejecucion, control_changes_file):
    """
    Gestiona un archivo CSV de control de cambios. Si el archivo no existe,
    lo crea con los datos de la nueva ejecución. Si existe, compara la columna
    'File_Name' entre el CSV existente y el nuevo DataFrame, e imprime las diferencias.
    El archivo existente NO se sobrescribe si ya existe.

    Args:
        df_nueva_ejecucion (pd.DataFrame): El DataFrame con los datos de la nueva ejecución
                                           (debe contener una columna 'File_Name').
        control_changes_file (str): El nombre del archivo CSV de control.
    """

    # Verificar si el archivo CSV ya existe
    if not os.path.exists(control_changes_file):
        # El CSV no existe, entonces lo creo y termino
        df_nueva_ejecucion.to_csv(control_changes_file, index=False, encoding='utf-8')

    else:
        # El CSV SÍ existe, entonces lo leo y comparo
        df_existente = pd.read_csv(control_changes_file)

        # Obtener los conjuntos de nombres de archivo para una comparación eficiente
        nombres_en_csv_existente = set(df_existente["File_Name"].tolist())
        nombres_en_nueva_ejecucion = set(df_nueva_ejecucion["File_Name"].tolist())

        # Nombres nuevos: los que están en la nueva ejecución pero no en el CSV
        archivos_nuevos = nombres_en_nueva_ejecucion - nombres_en_csv_existente
        if archivos_nuevos:
            print(f"\nArchivos NUEVOS")
            print("-" * 50) # Línea separadora
            for new_files in archivos_nuevos:
                print(f"- {new_files}")
            print("-" * 50, end='\n') # Línea separadora

        # Nombres que ya no están: los que estaban en el CSV pero no en la nueva ejecución
        archivos_eliminados = nombres_en_csv_existente - nombres_en_nueva_ejecucion
        if archivos_eliminados:
            print(f"\nArchivos ELIMINADOS")
            print("-" * 50) # Línea separadora
            for deleted_files in archivos_eliminados:
                print(f"- {deleted_files}")
            print("-" * 50, end='\n') # Línea separadora

        if archivos_nuevos or archivos_eliminados:
            print('\nSE ACTUALIZO LA BASE DE DATOS')
            df_nueva_ejecucion.to_csv(control_changes_file, index=False, encoding='utf-8')
        else:
            print('\nNO SE ACTUALIZO LA BASE DE DATOS')


def find_large_files_in_paths(paths_to_scan, min_size_mb=100):
    """
    Busca archivos mayores a 'min_size_mb' en las rutas proporcionadas.
    """
    min_size_bytes = min_size_mb * (1024**2) # Convierte MB a Bytes
    large_files = [] # Lista de archivos

    # Puedes añadir más nombres de subcarpetas si encuentras otras que no quieres escanear
    excluded_dirs = [
        'System Volume Information',
        '$Recycle.Bin',
        'Windows',
        'Recovery',
        'PerfLogs',
        'Drivers',
        'Config.Msi',
        'MSOCache',
    ]

    print(f"Buscando archivos mayores a {min_size_mb} MB en las rutas especificadas...")
    print("-" * 50) # Línea separadora
    print("⚠️  Carpetas excluidas por seguridad:")
    for subdir in excluded_dirs:
        print(f"    - {subdir}")
    print("-" * 50, end='\n\n') # Línea separadora

    # --- FASE 1: Recopilación de archivos grandes ---
    for path in paths_to_scan:
        if not os.path.isdir(path):
            print(f"\n**Advertencia**: La ruta '{path}' no existe o no es válida. Saltando esta ubicación.")
            continue

        # Contar directorios, ignorando los excluidos
        total_dirs = 0
        try:
            for _, dirnames, _ in os.walk(path):
                dirnames[:] = [d for d in dirnames if d not in excluded_dirs]
                total_dirs += len(dirnames) + 1 # +1 para el directorio actual
        except Exception as e:
            total_dirs = 0 # Si hay un error al contar, simplemente no mostramos el total exacto
            print(f"No se pudo obtener el conteo exacto de directorios en '{path}': {e}. La barra de progreso será en modo iteración.")

        # Recorrer la carpeta
        with tqdm(total=total_dirs if total_dirs > 0 else None,
                  desc=f"{path}: ",
                  unit="dir", leave=True) as pbar:

            for dirpath, dirnames, filenames in os.walk(path):
                '''
                dirpath: La ruta completa del directorio actual.
                dirnames: Una lista de los nombres de los subdirectorios que se encuentran directamente en dirpath.
                filenames: Una lista de los nombres de los archivos que se encuentran directamente en dirpath.
                '''
                # Filtrar los directorios excluidos
                dirnames[:] = [d for d in dirnames if d not in excluded_dirs]

                for filename in filenames:
                    file_path = os.path.join(dirpath, filename)
                    try:
                        if os.path.isfile(file_path):
                            file_size = os.path.getsize(file_path)
                            if file_size >= min_size_bytes:
                                large_files.append((file_size, file_path))
                    except OSError:
                        # Ignorar errores de acceso (permisos denegados, etc.)
                        pass
                pbar.update(1) # Actualiza la barra por cada directorio visitado

    # --- FASE 2: Procesamiento y presentación de resultados ---
    results = {
        'File_Name': [],
        'File_Size': []
    }
    large_files.sort(key=lambda x: x[0], reverse=True)

    print("\n\n--- Archivos grandes encontrados (ordenados por tamaño) ---")
    if not large_files:
        print(f"No se encontraron archivos mayores a {min_size_mb} MB en las rutas especificadas.")
    else:
        for size, path in large_files:
            # Formatear el tamaño para una mejor lectura
            if size > (1024**3):
                size_str = f"{size / (1024**3):.2f} GB"
            else:
                size_str = f"{size / (1024**2):.2f} MB"
            
            results['File_Name'].append(path)
            results['File_Size'].append(size)
            print(f"- {size_str}: {path}")

    # --- FASE 3: Guardar historico en un csv si no existe ---
    control_changes_file = 'control_changes.csv'

    # Crear un DataFrame a partir del diccionario
    df = pd.DataFrame(results)

    # Guardar el DataFrame a un archivo CSV
    gestionar_csv_cambios(df, control_changes_file)

# --- Configuración principal (modifica esto) ---
if __name__ == "__main__":
    my_paths = [
        'C:\\Users\\Gerardo',
        'C:\\Users\\Public',                                          
        'C:\\ProgramData',
        'C:\\Program Files',
    ]

    # Ejecuta la función principal
    find_large_files_in_paths(my_paths)