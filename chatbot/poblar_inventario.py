import os
import sys
import django

# Configurar entorno de Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chatbot.settings')
django.setup()

from app.models import Producto, MovimientoStock

PRODUCTOS = [
    {
        "sku": "GPU-NV-4090-ROG",
        "nombre": "ASUS ROG Strix GeForce RTX 4090 24GB OC Edition",
        "categoria": "Tarjetas Gráficas",
        "marca": "ASUS",
        "precio": 26839.88,
        "stock": 8,
        "stock_minimo": 2,
        "especificaciones": "24GB GDDR6X, 384-bit, PCIe 4.0, 16384 núcleos CUDA, Boost Clock 2640 MHz, 3.5 slots",
        "descripcion": "La tarjeta gráfica insignia definitiva para renderizado profesional 3D, IA y gaming extremo en 4K/8K.",
        "destacado": True
    },
    {
        "sku": "GPU-NV-4080S-MSI",
        "nombre": "MSI GeForce RTX 4080 Super 16GB Gaming X Slim",
        "categoria": "Tarjetas Gráficas",
        "marca": "MSI",
        "precio": 13419.88,
        "stock": 5,
        "stock_minimo": 3,
        "especificaciones": "16GB GDDR6X, 256-bit, PCIe 4.0, Tri Frozr 3, 10240 CUDA Cores, DLSS 3.5",
        "descripcion": "Rendimiento entusiasta con diseño delgado optimizado para chasis modernos y trazado de rayos completo.",
        "destacado": True
    },
    {
        "sku": "GPU-AMD-7900XTX-SAP",
        "nombre": "Sapphire Nitro+ AMD Radeon RX 7900 XTX 24GB",
        "categoria": "Tarjetas Gráficas",
        "marca": "Sapphire",
        "precio": 12199.88,
        "stock": 4,
        "stock_minimo": 2,
        "especificaciones": "24GB GDDR6, 384-bit, Arquitectura RDNA 3, Vapor Chamber, DisplayPort 2.1",
        "descripcion": "La GPU más poderosa de AMD para juegos en resolución 4K nativa con abundante VRAM.",
        "destacado": True
    },
    {
        "sku": "GPU-NV-4070TIS-GIG",
        "nombre": "Gigabyte GeForce RTX 4070 Ti Super Windforce OC 16GB",
        "categoria": "Tarjetas Gráficas",
        "marca": "Gigabyte",
        "precio": 10369.88,
        "stock": 8,
        "stock_minimo": 3,
        "especificaciones": "16GB GDDR6X, 256-bit, 3 ventiladores alternos de 90mm, placa trasera de metal",
        "descripcion": "Equilibrio ideal para gaming competitivo a 1440p y 4K con tecnología DLSS 3.",
        "destacado": False
    },
    {
        "sku": "GPU-NV-4060-ZOT",
        "nombre": "Zotac Gaming GeForce RTX 4060 8GB Twin Edge",
        "categoria": "Tarjetas Gráficas",
        "marca": "Zotac",
        "precio": 3659.88,
        "stock": 15,
        "stock_minimo": 5,
        "especificaciones": "8GB GDDR6, IceStorm 2.0 Cooling, Diseño ultra compacto de 2 ranuras",
        "descripcion": "Excelente opción de entrada para DLSS 3 y trazado de rayos a 1080p con bajo consumo.",
        "destacado": False
    },
    {
        "sku": "CPU-AMD-7950X3D",
        "nombre": "AMD Ryzen 9 7950X3D 16-Core con 3D V-Cache",
        "categoria": "Procesadores",
        "marca": "AMD",
        "precio": 7319.88,
        "stock": 4,
        "stock_minimo": 2,
        "especificaciones": "16 Núcleos, 32 Hilos, 128MB L3 Cache, TDP 120W, Socket AM5, 5.7 GHz Boost",
        "descripcion": "El pináculo para multitarea extrema, compilación pesada y máximo rendimiento gamer.",
        "destacado": True
    },
    {
        "sku": "CPU-INT-14900K",
        "nombre": "Intel Core i9-14900K 24 Núcleos 6.0GHz",
        "categoria": "Procesadores",
        "marca": "Intel",
        "precio": 6709.88,
        "stock": 6,
        "stock_minimo": 3,
        "especificaciones": "24 Núcleos (8P + 16E), 32 Hilos, 36MB Intel Smart Cache, Soporte PCIe 5.0 y DDR5",
        "descripcion": "Rendimiento sin concesiones para creadores audiovisuales y streaming profesional.",
        "destacado": False
    },
    {
        "sku": "CPU-AMD-7800X3D",
        "nombre": "AMD Ryzen 7 7800X3D 8-Core Gaming King",
        "categoria": "Procesadores",
        "marca": "AMD",
        "precio": 4757.88,
        "stock": 1,
        "stock_minimo": 4,
        "especificaciones": "8 Núcleos, 16 Hilos, 96MB 3D V-Cache, Socket AM5, 5.0 GHz Max Boost",
        "descripcion": "Considerado unánimemente el procesador más rápido del mundo para videojuegos.",
        "destacado": True
    },
    {
        "sku": "CPU-INT-14700K",
        "nombre": "Intel Core i7-14700K 20 Núcleos 5.6GHz",
        "categoria": "Procesadores",
        "marca": "Intel",
        "precio": 4635.88,
        "stock": 7,
        "stock_minimo": 3,
        "especificaciones": "20 Núcleos (8P + 12E), 28 Hilos, 33MB Cache, Gráficos UHD 770",
        "descripcion": "Potencia balanceada para productividad avanzada, renderizado y juegos pesados.",
        "destacado": False
    },
    {
        "sku": "CPU-AMD-7600X",
        "nombre": "AMD Ryzen 5 7600X 6-Core 5.3GHz",
        "categoria": "Procesadores",
        "marca": "AMD",
        "precio": 2683.88,
        "stock": 14,
        "stock_minimo": 5,
        "especificaciones": "6 Núcleos, 12 Hilos, 32MB L3 Cache, Socket AM5, PCIe 5.0",
        "descripcion": "La puerta de entrada ideal a la plataforma moderna AM5 y memorias DDR5.",
        "destacado": False
    },
    {
        "sku": "MB-ASU-Z790-HERO",
        "nombre": "ASUS ROG Maximus Z790 Dark Hero",
        "categoria": "Placas Madre",
        "marca": "ASUS",
        "precio": 7929.88,
        "stock": 2,
        "stock_minimo": 2,
        "especificaciones": "Socket LGA1700, 20+1 fases de poder, PCIe 5.0 M.2, Wi-Fi 7, Thunderbolt 4",
        "descripcion": "Placa madre de nivel entusiasta para overclocking extremo y componentes de élite.",
        "destacado": True
    },
    {
        "sku": "MB-MSI-X670E-ACE",
        "nombre": "MSI MEG X670E ACE E-ATX Motherboard",
        "categoria": "Placas Madre",
        "marca": "MSI",
        "precio": 7319.88,
        "stock": 3,
        "stock_minimo": 2,
        "especificaciones": "Socket AM5, 22+2+1 fases directas, LAN 10Gbps + 2.5Gbps, Wi-Fi 6E, 4 ranuras M.2",
        "descripcion": "Construcción masiva blindada con disipación superior para procesadores Ryzen serie 7000/9000.",
        "destacado": False
    },
    {
        "sku": "MB-ASU-X670E-TUF",
        "nombre": "ASUS TUF Gaming X670E-PLUS WiFi",
        "categoria": "Placas Madre",
        "marca": "ASUS",
        "precio": 3537.88,
        "stock": 7,
        "stock_minimo": 3,
        "especificaciones": "Socket AM5, 14+2 etapas de potencia en equipo, USB 3.2 Gen 2x2 Type-C",
        "descripcion": "Componentes de grado militar TUF certificados para máxima durabilidad.",
        "destacado": False
    },
    {
        "sku": "MB-MSI-B650-TMH",
        "nombre": "MSI MAG B650 Tomahawk WiFi",
        "categoria": "Placas Madre",
        "marca": "MSI",
        "precio": 2683.88,
        "stock": 10,
        "stock_minimo": 4,
        "especificaciones": "Socket AM5, DDR5, Audio Boost 5, Realtek 2.5G LAN, disipadores extendidos",
        "descripcion": "La placa madre AM5 B650 más balanceada y recomendada del mercado.",
        "destacado": True
    },
    {
        "sku": "MB-GIG-A520M-K",
        "nombre": "Gigabyte A520M K V2 Ultra Durable",
        "categoria": "Placas Madre",
        "marca": "Gigabyte",
        "precio": 853.88,
        "stock": 0,
        "stock_minimo": 5,
        "especificaciones": "Micro-ATX, Socket AM4, PCIe 3.0 x4 M.2, GbE LAN con gestión de ancho de banda",
        "descripcion": "Solución ultra económica para oficinas y ensamble de gama de entrada.",
        "destacado": False
    },
    {
        "sku": "RAM-GSK-TZ5-64",
        "nombre": "G.Skill Trident Z5 RGB 64GB (2x32GB) DDR5 6400MHz",
        "categoria": "Memorias RAM",
        "marca": "G.Skill",
        "precio": 3049.88,
        "stock": 4,
        "stock_minimo": 2,
        "especificaciones": "64GB Kit (2x32GB), DDR5 6400MHz, CL32-39-39-102, Intel XMP 3.0",
        "descripcion": "Capacidad masiva y latencias ultrabajas para estaciones de trabajo y edición pesada.",
        "destacado": True
    },
    {
        "sku": "RAM-COR-DOM-32",
        "nombre": "Corsair Dominator Titanium RGB 32GB (2x16GB) DDR5 6600MHz",
        "categoria": "Memorias RAM",
        "marca": "Corsair",
        "precio": 2317.88,
        "stock": 6,
        "stock_minimo": 3,
        "especificaciones": "32GB (2x16GB), DDR5 6600MHz, CL32, Chips seleccionados a mano DHX Cooling",
        "descripcion": "El pináculo del diseño y disipación térmica con barras superiores intercambiables.",
        "destacado": False
    },
    {
        "sku": "RAM-KNG-RNG-32",
        "nombre": "Kingston Fury Renegade RGB 32GB (2x16GB) DDR5 6000MHz",
        "categoria": "Memorias RAM",
        "marca": "Kingston",
        "precio": 1829.88,
        "stock": 8,
        "stock_minimo": 3,
        "especificaciones": "32GB (2x16GB), DDR5 6000MHz, CL32, Sincronización infrarroja patentada",
        "descripcion": "Rendimiento agresivo con espectacular barra de luz dinámica.",
        "destacado": False
    },
    {
        "sku": "RAM-COR-VEN-32",
        "nombre": "Corsair Vengeance RGB 32GB (2x16GB) DDR5 6000MHz CL30",
        "categoria": "Memorias RAM",
        "marca": "Corsair",
        "precio": 1463.88,
        "stock": 14,
        "stock_minimo": 5,
        "especificaciones": "32GB (2x16GB), DDR5 6000MHz, Latencia dulce CL30-36-36-76, AMD EXPO",
        "descripcion": "El kit predilecto optimizado para procesadores AMD Ryzen serie 7000.",
        "destacado": True
    },
    {
        "sku": "RAM-CRU-8GB-D4",
        "nombre": "Crucial 8GB DDR4 3200MHz UDIMM",
        "categoria": "Memorias RAM",
        "marca": "Crucial",
        "precio": 243.88,
        "stock": 25,
        "stock_minimo": 5,
        "especificaciones": "1x8GB, DDR4 3200MHz, CL22, 1.2V, 288-pin UDIMM",
        "descripcion": "El componente con el precio más bajo de toda nuestra tienda de tecnología.",
        "destacado": False
    },
    {
        "sku": "SSD-SAM-990P-4TB",
        "nombre": "Samsung 990 PRO 4TB PCIe 4.0 NVMe M.2 con Disipador",
        "categoria": "Almacenamiento",
        "marca": "Samsung",
        "precio": 4269.88,
        "stock": 3,
        "stock_minimo": 2,
        "especificaciones": "4TB, Lectura hasta 7,450 MB/s, Escritura hasta 6,900 MB/s, Compatible PS5",
        "descripcion": "Máxima capacidad y velocidad para bibliotecas masivas de juegos y proyectos de cine.",
        "destacado": True
    },
    {
        "sku": "SSD-CRU-T700-2TB",
        "nombre": "Crucial T700 2TB PCIe 5.0 NVMe SSD (12,400 MB/s)",
        "categoria": "Almacenamiento",
        "marca": "Crucial",
        "precio": 3415.88,
        "stock": 4,
        "stock_minimo": 2,
        "especificaciones": "2TB, PCIe Gen5 x4, Lectura 12,400 MB/s, Disipador pasivo de cobre premium",
        "descripcion": "Velocidad vertiginosa de última generación para transferencias instantáneas de datos.",
        "destacado": True
    },
    {
        "sku": "HDD-SEA-IRON-8TB",
        "nombre": "Seagate IronWolf Pro 8TB NAS HDD 7200 RPM",
        "categoria": "Almacenamiento",
        "marca": "Seagate",
        "precio": 2439.88,
        "stock": 6,
        "stock_minimo": 2,
        "especificaciones": "8TB, SATA 6Gb/s, 7200 RPM, 256MB Cache, Sensores RV para servidores NAS",
        "descripcion": "Diseñado para funcionamiento ininterrumpido 24/7 y copias de seguridad masivas.",
        "destacado": False
    },
    {
        "sku": "SSD-WD-SN850X-2TB",
        "nombre": "Western Digital Black SN850X 2TB NVMe M.2",
        "categoria": "Almacenamiento",
        "marca": "Western Digital",
        "precio": 2073.88,
        "stock": 8,
        "stock_minimo": 3,
        "especificaciones": "2TB, Lectura 7,300 MB/s, Modo Gaming 2.0 en software WD_BLACK",
        "descripcion": "Uno de los discos favoritos de la comunidad gamer por su confiabilidad y rapidez.",
        "destacado": False
    },
    {
        "sku": "SSD-SAM-990P-2TB",
        "nombre": "Samsung 990 PRO 2TB PCIe 4.0 NVMe M.2",
        "categoria": "Almacenamiento",
        "marca": "Samsung",
        "precio": 1951.88,
        "stock": 10,
        "stock_minimo": 4,
        "especificaciones": "2TB, V-NAND TLC, Controlador Samsung Pascal, 2GB LPDDR4 DRAM Cache",
        "descripcion": "Excelente rendimiento sostenido para edición de video 4K y cargas inmediatas.",
        "destacado": False
    },
    {
        "sku": "PSU-COR-AX1600I",
        "nombre": "Corsair AX1600i 1600W 80 Plus Titanium Digital",
        "categoria": "Fuentes de Poder",
        "marca": "Corsair",
        "precio": 7319.88,
        "stock": 2,
        "stock_minimo": 1,
        "especificaciones": "1600W, Eficiencia 80+ Titanium (>94%), Transistores de nitruro de galio (GaN)",
        "descripcion": "La fuente de poder más avanzada del planeta para servidores y estaciones multi-GPU.",
        "destacado": True
    },
    {
        "sku": "PSU-SEA-TX1300",
        "nombre": "Seasonic Prime TX-1300 1300W 80 Plus Titanium ATX 3.0",
        "categoria": "Fuentes de Poder",
        "marca": "Seasonic",
        "precio": 5489.88,
        "stock": 3,
        "stock_minimo": 2,
        "especificaciones": "1300W, Totalmente modular, Cable nativo 12VHPWR PCIe 5.0, 12 años de garantía",
        "descripcion": "Construcción japonesa intransigente con regulación de voltaje ultra precisa.",
        "destacado": False
    },
    {
        "sku": "PSU-ASU-THOR-1000",
        "nombre": "ASUS ROG Thor 1000W Platinum II OLED",
        "categoria": "Fuentes de Poder",
        "marca": "ASUS",
        "precio": 4025.88,
        "stock": 4,
        "stock_minimo": 2,
        "especificaciones": "1000W, 80 Plus Platinum, Pantalla OLED con consumo de watts en tiempo real",
        "descripcion": "Visualización estética impecable para gabinetes con ventana de fuente visible.",
        "destacado": True
    },
    {
        "sku": "PSU-BEQ-DP13-1000",
        "nombre": "be quiet! Dark Power Pro 13 1000W Titanium ATX 3.0",
        "categoria": "Fuentes de Poder",
        "marca": "be quiet!",
        "precio": 3659.88,
        "stock": 4,
        "stock_minimo": 2,
        "especificaciones": "1000W, Certificación 80 Plus Titanium, Ventilador Silent Wings sin marco",
        "descripcion": "Operación acústicamente inaudible incluso bajo cargas intensas de trabajo.",
        "destacado": False
    },
    {
        "sku": "PSU-COR-RM1000X",
        "nombre": "Corsair RM1000x Shift 1000W 80 Plus Gold Modular",
        "categoria": "Fuentes de Poder",
        "marca": "Corsair",
        "precio": 2439.88,
        "stock": 7,
        "stock_minimo": 3,
        "especificaciones": "1000W, 80 Plus Gold, Conectores modulares laterales patentados para fácil armado",
        "descripcion": "Innovadora disposición lateral de cables para una gestión impecable en el gabinete.",
        "destacado": False
    },
    {
        "sku": "REF-ASU-RYU3-360",
        "nombre": "ASUS ROG Ryujin III 360 ARGB Refrigeración Líquida LCD",
        "categoria": "Refrigeración",
        "marca": "ASUS",
        "precio": 4269.88,
        "stock": 2,
        "stock_minimo": 2,
        "especificaciones": "Radiador 360mm, Pantalla LCD de 3.5 pulgadas personalizable a 60 FPS, Bomba Asetek 8va Gen",
        "descripcion": "La cúspide de la refrigeración AIO con ventilador integrado para disipar los VRMs.",
        "destacado": True
    },
    {
        "sku": "REF-NZX-KRAK-360",
        "nombre": "NZXT Kraken Elite 360 RGB LCD Display",
        "categoria": "Refrigeración",
        "marca": "NZXT",
        "precio": 3415.88,
        "stock": 4,
        "stock_minimo": 2,
        "especificaciones": "Radiador 360mm, Pantalla gran angular de 2.36 pulgadas, Ventiladores F120 RGB Core",
        "descripcion": "Monitoreo en vivo de temperaturas del CPU/GPU o GIFs animados con estilo minimalista.",
        "destacado": False
    },
    {
        "sku": "REF-COR-H150I-LNK",
        "nombre": "Corsair iCUE LINK H150i RGB 360mm",
        "categoria": "Refrigeración",
        "marca": "Corsair",
        "precio": 2927.88,
        "stock": 5,
        "stock_minimo": 2,
        "especificaciones": "Radiador 360mm, Sistema de conexión de un solo cable iCUE LINK, Pasta preaplicada XTM70",
        "descripcion": "Revolucionario ecosistema que reduce drásticamente el desorden de cables en el chasis.",
        "destacado": False
    },
    {
        "sku": "REF-DPC-LT720",
        "nombre": "DeepCool LT720 360mm High-Performance Liquid Cooler",
        "categoria": "Refrigeración",
        "marca": "DeepCool",
        "precio": 1585.88,
        "stock": 9,
        "stock_minimo": 3,
        "especificaciones": "Radiador 360mm, Bomba multidimensional de espejo infinito con microcanales mejorados",
        "descripcion": "Disipación masiva capaz de domar procesadores Intel i9 y Ryzen 9 a precio imbatible.",
        "destacado": True
    },
    {
        "sku": "REF-ARC-LF3-360",
        "nombre": "Arctic Liquid Freezer III 360 A-RGB Black",
        "categoria": "Refrigeración",
        "marca": "Arctic",
        "precio": 1463.88,
        "stock": 8,
        "stock_minimo": 3,
        "especificaciones": "Radiador extra grueso de 38mm, Ventilador VRM de 60mm integrado en la bomba",
        "descripcion": "Uno de los disipadores líquidos más eficientes y silenciosos reconocidos por expertos.",
        "destacado": False
    },
    {
        "sku": "CAS-LIA-O11D-EVOXL",
        "nombre": "Lian Li O11 Dynamic EVO XL RGB Full Tower",
        "categoria": "Gabinetes",
        "marca": "Lian Li",
        "precio": 2927.88,
        "stock": 3,
        "stock_minimo": 2,
        "especificaciones": "Full Tower, Cristal templado dual panorámico, Soporte para radiadores triples de 420mm",
        "descripcion": "El chasis predilecto para armados personalizados de refrigeración líquida custom.",
        "destacado": True
    },
    {
        "sku": "CAS-FRA-NORTH-XL",
        "nombre": "Fractal Design North XL Charcoal Black con Madera Real",
        "categoria": "Gabinetes",
        "marca": "Fractal Design",
        "precio": 2317.88,
        "stock": 4,
        "stock_minimo": 2,
        "especificaciones": "Frontal con lamas de nogal natural certificado FSC, Soporte E-ATX y GPU hasta 413mm",
        "descripcion": "Diseño escandinavo sofisticado que combina alta tecnología con calidez natural.",
        "destacado": True
    },
    {
        "sku": "CAS-BEQ-SB800-FX",
        "nombre": "be quiet! Shadow Base 800 FX Black",
        "categoria": "Gabinetes",
        "marca": "be quiet!",
        "precio": 2317.88,
        "stock": 3,
        "stock_minimo": 2,
        "especificaciones": "4 ventiladores Light Wings PWM ARGB de 140mm incluidos, Frontal de malla de alto flujo",
        "descripcion": "Excelente flujo de aire con iluminación discreta y espacio de trabajo generoso.",
        "destacado": False
    },
    {
        "sku": "CAS-HYT-Y60-PAN",
        "nombre": "Hyte Y60 Panoramic Tempered Glass White",
        "categoria": "Gabinetes",
        "marca": "Hyte",
        "precio": 2195.88,
        "stock": 5,
        "stock_minimo": 2,
        "especificaciones": "Diseño de 3 piezas de vidrio panorámico sin esquinas, Cable Riser PCIe 4.0 incluido",
        "descripcion": "Muestra tu tarjeta gráfica verticalmente en una vitrina estética sin obstáculos.",
        "destacado": True
    },
    {
        "sku": "CAS-COR-5000D-AF",
        "nombre": "Corsair 5000D Airflow Mid-Tower Tempered Glass",
        "categoria": "Gabinetes",
        "marca": "Corsair",
        "precio": 2012.88,
        "stock": 7,
        "stock_minimo": 3,
        "especificaciones": "Mid-Tower, Sistema de gestión de cables RapidRoute, Panel frontal de acero perforado",
        "descripcion": "Estructura sólida con ventilación excepcional para hardware de alta gama.",
        "destacado": False
    },
    {
        "sku": "MON-SAM-G9-NEO",
        "nombre": "Samsung Odyssey Neo G9 49 Pulgadas Curvo Dual QHD 240Hz Mini-LED",
        "categoria": "Monitores",
        "marca": "Samsung",
        "precio": 18299.88,
        "stock": 2,
        "stock_minimo": 1,
        "especificaciones": "49\" Ultra-Wide (5120x1440), Curvatura 1000R, Quantum Mini-LED, 240Hz, 1ms, HDR2000",
        "descripcion": "Experiencia panorámica envolvente equivalente a dos monitores QHD de 27 pulgadas sin marcos.",
        "destacado": True
    },
    {
        "sku": "MON-ASU-PG32UCDM",
        "nombre": "ASUS ROG Swift OLED PG32UCDM 32 Pulgadas 4K 240Hz",
        "categoria": "Monitores",
        "marca": "ASUS",
        "precio": 15859.88,
        "stock": 2,
        "stock_minimo": 1,
        "especificaciones": "32\" 4K UHD (3840x2160), QD-OLED de 3ra generación, 240Hz, 0.03ms, Disipador de grafeno",
        "descripcion": "Claridad insuperable, negros puros y velocidad absoluta para eSports y cine.",
        "destacado": True
    },
    {
        "sku": "MON-DEL-AW3423DWF",
        "nombre": "Dell Alienware AW3423DWF 34 Pulgadas QD-OLED Curvo",
        "categoria": "Monitores",
        "marca": "Dell",
        "precio": 9759.88,
        "stock": 3,
        "stock_minimo": 2,
        "especificaciones": "34\" WQHD (3440x1440), Curvatura 1800R, QD-OLED, 165Hz, Cobertura 99.3% DCI-P3",
        "descripcion": "Colores cinematográficos vibrantes con contraste infinito y certificación HDR TrueBlack 400.",
        "destacado": False
    },
    {
        "sku": "MON-LG-27GR95QE",
        "nombre": "LG UltraGear OLED 27GR95QE-B 27 Pulgadas QHD 240Hz",
        "categoria": "Monitores",
        "marca": "LG",
        "precio": 9149.88,
        "stock": 4,
        "stock_minimo": 2,
        "especificaciones": "27\" 1440p QHD, Panel OLED, 240Hz, 0.03ms GtG, HDMI 2.1, DisplayPort 1.4",
        "descripcion": "El monitor competitivo predilecto para shooters profesionales de ritmo vertiginoso.",
        "destacado": False
    },
    {
        "sku": "MON-AOC-24G2SP",
        "nombre": "AOC Gaming 24G2SP 24 Pulgadas IPS 165Hz 1080p",
        "categoria": "Monitores",
        "marca": "AOC",
        "precio": 1707.88,
        "stock": 14,
        "stock_minimo": 5,
        "especificaciones": "23.8\" Full HD (1920x1080), Panel IPS, 165Hz, 1ms MPRT, FreeSync Premium",
        "descripcion": "El mejor monitor calidad-precio para jugadores de esports a 1080p.",
        "destacado": False
    },
    {
        "sku": "PER-COR-K70MAX",
        "nombre": "Corsair K70 MAX RGB Teclado Magnético Mecánico",
        "categoria": "Periféricos",
        "marca": "Corsair",
        "precio": 2805.88,
        "stock": 5,
        "stock_minimo": 2,
        "especificaciones": "Switches magnéticos CORSAIR MGX ajustables (0.4mm a 3.6mm), Reposamuñecas viscoelástico",
        "descripcion": "Puntos de actuación ajustables por tecla para pulsaciones ultra rápidas personalizables.",
        "destacado": True
    },
    {
        "sku": "PER-KEY-Q1PRO",
        "nombre": "Keychron Q1 Pro Teclado Mecánico Custom QMK/VIA",
        "categoria": "Periféricos",
        "marca": "Keychron",
        "precio": 2439.88,
        "stock": 4,
        "stock_minimo": 2,
        "especificaciones": "Cuerpo completo de aluminio CNC, Montaje doble Gasket, Switches Banana lubricados, Bluetooth 5.1",
        "descripcion": "La cúspide del sonido acústico y tacto artesanal para entusiastas de la escritura.",
        "destacado": False
    },
    {
        "sku": "PER-STE-APEXTKL",
        "nombre": "SteelSeries Apex Pro TKL Teclado con Switches OmniPoint 2.0",
        "categoria": "Periféricos",
        "marca": "SteelSeries",
        "precio": 2317.88,
        "stock": 6,
        "stock_minimo": 2,
        "especificaciones": "Switches ajustables OmniPoint 2.0 (Rapid Trigger), Pantalla inteligente OLED",
        "descripcion": "La ventaja competitiva máxima en CS2, Valorant y Fortnite gracias a Rapid Trigger.",
        "destacado": True
    },
    {
        "sku": "PER-LOG-G502XPLUS",
        "nombre": "Logitech G502 X PLUS LIGHTSPEED RGB Mouse",
        "categoria": "Periféricos",
        "marca": "Logitech",
        "precio": 1707.88,
        "stock": 10,
        "stock_minimo": 4,
        "especificaciones": "13 controles programables, Rueda de desplazamiento hiperrápida de doble modo, LIGHTSYNC RGB",
        "descripcion": "La evolución del ratón gamer más vendido y ergonómico del mundo.",
        "destacado": False
    },
    {
        "sku": "PER-STE-QCK-XXL",
        "nombre": "SteelSeries QcK Heavy XXL Pad Mouse Gaming (900x400x4mm)",
        "categoria": "Periféricos",
        "marca": "SteelSeries",
        "precio": 365.88,
        "stock": 30,
        "stock_minimo": 8,
        "especificaciones": "Dimensiones 900 x 400 x 4 mm, Paño microtejido legendario QcK, Base de goma extra gruesa",
        "descripcion": "Superficie de tela optimizada para movimientos de rastreo de baja y alta sensibilidad.",
        "destacado": False
    }
]

def poblar():
    print(f'Iniciando carga de {len(PRODUCTOS)} productos tecnológicos...')
    creados = 0
    actualizados = 0

    # Asegurar catálogo exacto de 50 productos
    codigos_validos = [p['sku'] for p in PRODUCTOS]
    Producto.objects.exclude(codigo__in=codigos_validos).delete()

    for data in PRODUCTOS:
        data_clean = dict(data)
        codigo = data_clean.pop('sku')
        stock = data_clean.pop('stock', 0)
        data_clean['cantidad_existente'] = stock
        data_clean['estado'] = True

        obj, created = Producto.objects.update_or_create(
            codigo=codigo,
            defaults=data_clean
        )
        if created:
            creados += 1
            if obj.cantidad_existente > 0:
                MovimientoStock.objects.create(
                    producto=obj,
                    tipo='ENTRADA',
                    cantidad=obj.cantidad_existente,
                    stock_previo=0,
                    stock_resultante=obj.cantidad_existente,
                    motivo='Inventario inicial y apertura de almacén',
                    usuario='Sistema'
                )
        else:
            actualizados += 1

    total = Producto.objects.count()
    print('-> Proceso completado exitosamente:')
    print(f'   * Productos creados: {creados}')
    print(f'   * Productos actualizados: {actualizados}')
    print(f'   * Total de productos en base de datos: {total}')

    mas_caro = Producto.objects.order_by('-precio').first()
    if mas_caro:
        print(f'   * Producto con el precio más alto: [{mas_caro.sku}] {mas_caro.nombre} (Bs. {mas_caro.precio})')

    mas_barato = Producto.objects.order_by('precio').first()
    if mas_barato:
        print(f'   * Producto con el precio más bajo: [{mas_barato.sku}] {mas_barato.nombre} (Bs. {mas_barato.precio})')

if __name__ == '__main__':
    poblar()
