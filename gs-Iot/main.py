import mediapipe as mp
from ultralytics import YOLO
import cv2

model = YOLO('yolov8n.pt') # modelo YOLO para detectar pessoas

cap = cv2.VideoCapture('video.mp4')
if not cap.isOpened():
    print("Erro ao abrir o vídeo.")
    exit()
# abre o vídeo

mp_pose = mp.solutions.pose
mp_draw = mp.solutions.drawing_utils
pose = mp_pose.Pose(static_image_mode=False)
# configuração do midiapipe

skip_frames = 3 # Fator de aceleração: pular n frames

while cap.isOpened():
    for _ in range(skip_frames):
        cap.read()  # Pula frames

    ret, frame = cap.read()
    if not ret:
        break
    # le cada frame (imagem) e se não conseguiu ler para o código

    frame_resized = cv2.resize(frame, None, fx=1, fy=1) # redimensiona o tamanho do vídeo passando cada frame
    results = model(frame_resized) # lista de results  
    detections = results[0] # objeto com todas as detecções da sua imagem
    boxes = detections.boxes.xyxy # array com objetos tensor com os bounding boxes
    # exemplo de boxes: tensor([50.0, 100.0, 200.0, 300.0])
    classes = detections.boxes.cls # 0 é person, 2 é dog
    # tensor([0., 2.])
    
    person_boxes = [box for box, cls in zip(boxes, classes) if int(cls) == 0]
    # person_boxes tem as coordenadas de somente as pessoas (não tem o recorte)
    # print(f"person_boxes - {person_boxes}") # [tensor([ 281.0838,  486.3299,  541.0790, 1003.5989])]
    person_boxes = [[int(coord) for coord in box] for box in person_boxes] # outra forma de deixar int
    #print(f"formato do person-boxes: {person_boxes.shape}")
    
    qtd = len(person_boxes)

    if qtd == 0:
        status = "situação segura."
    elif qtd == 1:
        status = "situação estável"
    elif qtd == 2:
        status = "atenção moderada"
    else: 
        status = "atenção máxima"

    print(f"Pessoas detectadas: {qtd} - {status}")

    annotated_frame = frame_resized.copy() # Cria uma cópia do frame para desenhar só as pessoas

    person_crops = []

    for box in person_boxes: # só atua quando o midiapipe identifica alguma pessoa
        x_min, y_min, x_max, y_max = box # converteu antes o person_boxes para int
        #print(f"Coordenadas - {[x_min, y_min, x_max, y_max]}") # [648, 485, 839, 900]
        cv2.rectangle(annotated_frame, (x_min, y_min), (x_max, y_max), (0, 255, 0), 2) # Desenha um retângulo verde só nas pessoas
        crop = frame[y_min:y_max, x_min:x_max] 
        person_crops.append(crop) # box são as coordenadas
    # person_crops tem o recorte de cada pessoa detectada no frame no formato 3D 
    

    for idx, (box, crop) in enumerate(zip(person_boxes, person_crops)):
        x_min, y_min, x_max, y_max = box
        crop_rgb = cv2.cvtColor(crop, cv2.COLOR_BGR2RGB) # Converte o crop para RGB exigido pelo Midiapipe

        results = pose.process(crop_rgb) # contém as coordenadas dos landmarks detectados, se houver
        
        # Verificar se encontrou landmarks:
        """if results.pose_landmarks:
            print(f"Pessoa {idx}: Landmarks detectados")
        else:
            print(f"Pessoa {idx}: Nenhum landmark detectado")"""
        
        if results.pose_landmarks:
            # mp.solutions.drawing_utils.draw_landmarks(crop, results.pose_landmarks, mp.solutions.pose.POSE_CONNECTIONS)
            #print(f"crop - {crop}")
            mp_draw.draw_landmarks(crop, results.pose_landmarks, mp_pose.POSE_CONNECTIONS) # desenha os landmarks

        # talvez precise tratar quando o novo recorte for maior ou menor que o recorte original
        h, w = y_max - y_min, x_max - x_min
        if crop.shape[:2] != (h, w):
            crop = cv2.resize(crop, (w, h))


        annotated_frame[y_min:y_max, x_min:x_max] = crop	# coloca o crop já com landmarks de volta no lugar correto	 
					
    display_frame = cv2.resize(annotated_frame, None, fx=0.5, fy=0.5)
    cv2.imshow('YOLO Detection', display_frame)

    if cv2.waitKey(10) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
  
			
