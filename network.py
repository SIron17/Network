import random
import numpy as np
import matplotlib.pyplot as plt
import os

# 네트워크 세미나 시뮬레이션 환경 구성
# 기존 EBO의 경우 우선 순위 범위가 RA-RU의 수만큼 사용

NUM_SIM = 1
NUM_DTI = 100000
simulation_list = []

# AP set
SIFS = 16
DIFS = 32
NUM_RU = 8
PACKET_SIZE = 1000
TF_SIZE = 89
DATA_RATE = 1
BA_SIZE = 32
DTI = 32

# 기본 설정 파라미터 값
RU = 8
MIN_OCW = 8
MAX_OCW = 64
RETRY_BS = 10

# Transmission time in us
PKT_SZ_us = (PACKET_SIZE * 8) / (DATA_RATE * 1000)
TF_SZ_us = (TF_SIZE * 8) / (DATA_RATE * 1000)
BA_SZ_us = (BA_SIZE * 8) / (DATA_RATE * 1000)
TWT_INTERVAL = DIFS + TF_SZ_us + SIFS * 2 + DTI + BA_SZ_us

# 성능 변수
Stats_PKT_TX_Trial = 0
Stats_PKT_Success = 0
Stats_PKT_Collision = 0
Stats_PKT_Delay = 0

Stats_RU_TX_Trial = 0
Stats_RU_Idle = 0
Stats_RU_Success = 0
Stats_RU_Collision = 0

stationList = []

PKS_throughput_results = []
PKS_coll_results = []
PKS_dealy_results = []

RU_idle_results = []
RU_Success_results = []
RU_coll_results = []

x_list = []

class Station:
    def __init__(self):
        self.ru = 0
        self.cw = MIN_OCW
        self.bo = random.randrange(0, self.cw)
        self.tx_status = False
        self.suc_status = False
        self.delay = 0
        self.retry = 0
        self.data_size = 0

def createSTA(USER):
    for i in range(0, USER):
        sta = Station()
        stationList.append(sta)

def allocationRA_RU():
    for sta in stationList:
        if (sta.bo <= 0):
            sta.tx_status = True
            sta.ru = random.randrange(0, NUM_RU)
        else:
            sta.bo -= NUM_RU
            sta.tx_status = False

def setSuccess(ru):
    for sta in stationList:
        if (sta.tx_status == True):
            if (sta.ru == ru):
                sta.suc_status = True

def setCollision(ru):
    for sta in stationList:
        if (sta.tx_status == True):
            if (sta.ru == ru):
                sta.suc_status = False

def incRUTX():
    global Stats_RU_TX_Trial
    Stats_RU_TX_Trial += 1

def incRUCollision():
    global Stats_RU_Collision
    Stats_RU_Collision += 1

def incRUSuccess():
    global Stats_RU_Success
    Stats_RU_Success += 1

def incRUIdle():
    global Stats_RU_Idle
    Stats_RU_Idle += 1

def checkCollision():
    coll_RU = []
    for i in range(0, NUM_RU):
        coll_RU.append(0)
    for sta in stationList:
        if (sta.tx_status == True):
            coll_RU[int(sta.ru)] += 1

    for i in range(0, RU):
        incRUTX()
        if (coll_RU[i] == 1):
            setSuccess(i)
            incRUSuccess()
        elif (coll_RU[i] <= 0):
            incRUIdle()
        else:
            setCollision(i)
            incRUCollision()

def addStats():
    global Stats_PKT_TX_Trial
    global Stats_PKT_Success
    global Stats_PKT_Collision
    global Stats_PKT_Delay

    for sta in stationList:
        if (sta.tx_status == True):
            Stats_PKT_TX_Trial += 1
            if (sta.suc_status == True):
                Stats_PKT_Success += 1
                Stats_PKT_Delay += sta.delay
            else:
                Stats_PKT_Collision += 1

def incTrial():
    for sta in stationList:
        sta.delay += 1

def changeStaVariables():
    for sta in stationList:
        if (sta.tx_status == True):
            if (sta.suc_status == True):
                sta.ru = 0
                sta.cw = MIN_OCW
                sta.bo = random.randrange(0, sta.cw)
                sta.tx_status = False
                sta.suc_status = False
                sta.delay = 0
                sta.retry = 0
                sta.data_sz = 0
            else:
                sta.ru = 0
                sta.retry += 1
                if (sta.retry >= RETRY_BS):
                    sta.cw = MIN_OCW
                    sta.retry = 0
                    sta.delay = 0
                    sta.data_sz = 0
                else:
                    sta.cw *= 2
                    if (sta.cw > MAX_OCW):
                        sta.cw = MAX_OCW
                sta.bo = random.randrange(0, sta.cw)
                sta.tx_status = False
                sta.suc_status = False


def print_Performance():
    # 패킷 단위 성능
    PKS_coll_rate = 0
    PKS_throughput = 0
    PKS_delay = 0

    print("[패킷 단위 성능]")
    print("전송 시도 수 : ", Stats_PKT_TX_Trial)

    if Stats_PKT_TX_Trial > 0:
        print("전송 성공 수 : ", Stats_PKT_Success)
        print("전송 실패 수 : ", Stats_PKT_Collision)

        PKS_coll_rate = (Stats_PKT_Collision / Stats_PKT_TX_Trial) * 100
        PKS_throughput = (Stats_PKT_Success * PACKET_SIZE * 8) / (NUM_SIM * NUM_DTI * TWT_INTERVAL)
        PKS_delay = (Stats_PKT_Delay / Stats_PKT_Success) * TWT_INTERVAL

        print("충돌율 : ", PKS_coll_rate)
        print("지연 : ", PKS_delay)
        print(">> 통신 속도 : ", PKS_throughput)  # 단위: Mbps
        print(">> 지연 : ", PKS_delay)  # 단위: us
    else:
        print("전송 시도가 없습니다.")

    # RU 단위 성능
    RU_idle_rate = 0
    RU_Success_rate = 0
    RU_Collision_rate = 0

    print("[RU 단위 성능]")

    if Stats_RU_TX_Trial > 0:
        RU_idle_rate = (Stats_RU_Idle / Stats_RU_TX_Trial) * 100
        RU_Success_rate = (Stats_RU_Success / Stats_RU_TX_Trial) * 100
        RU_Collision_rate = (Stats_RU_Collision / Stats_RU_TX_Trial) * 100

        print("전송 시도 수 : ", Stats_RU_TX_Trial)
        print("전송 성공 수 : ", Stats_RU_Success)
        print("전송 실패 수 : ", Stats_RU_Collision)
        print("Idle 수 : ", Stats_RU_Idle)
        print("Idle 비율 : ", RU_idle_rate)
        print("성공율 : ", RU_Success_rate)
        print(">> 충돌율 : ", RU_Collision_rate)
    else:
        print("전송 시도가 없습니다.")

    # 성능 결과 리스트에 저장
    PKS_coll_results.append(PKS_coll_rate)
    PKS_throughput_results.append(PKS_throughput)
    PKS_dealy_results.append(PKS_delay)

    RU_idle_results.append(RU_idle_rate)
    RU_Success_results.append(RU_Success_rate)
    RU_coll_results.append(RU_Collision_rate)

def print_graph():
    for i in range(1, USER_MAX + 1):
        x_list.append(i)

    plt.figure(figsize=(20, 10))

    plt.subplot(231)
    plt.plot(x_list, PKS_throughput_results, color='red', marker='o')
    plt.title('Packet Throughput')
    plt.xlabel('Number or STA')
    plt.ylabel('throughput')

    plt.subplot(232)
    plt.plot(x_list, PKS_coll_results, color='red', marker='o')
    plt.title('Packet Collision Rate')
    plt.xlabel('Number or STA')
    plt.ylabel('collision rate')

    plt.subplot(233)
    plt.plot(x_list, PKS_dealy_results, color='red', marker='o')
    plt.title('Packet delay')
    plt.xlabel('Number or STA')
    plt.ylabel('delay')

    plt.subplot(234)
    plt.plot(x_list, RU_idle_results, color='red', marker='o')
    plt.title('RU idle rate')
    plt.xlabel('Number or STA')
    plt.ylabel('idle rate')

    plt.subplot(235)
    plt.plot(x_list, RU_Success_results, color='red', marker='o')
    plt.title('RU Success rate')
    plt.xlabel('Number or STA')
    plt.ylabel('success rate')

    plt.subplot(236)
    plt.plot(x_list, RU_coll_results, color='red', marker='o')
    plt.title('RU collision rate')
    plt.xlabel('Number or STA')
    plt.ylabel('collision rate')

    plt.show()
    plt.close()

def save():
    global simulation_list

    simulation_list.append(PKS_throughput_results)
    simulation_list.append(PKS_coll_results)
    simulation_list.append(PKS_dealy_results)
    simulation_list.append(RU_idle_results)
    simulation_list.append(RU_Success_results)
    simulation_list.append(RU_coll_results)

    # 현재 실행 중인 .py 파일이 있는 디렉토리에 'data' 폴더 생성
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(script_dir, 'data')
    os.makedirs(data_dir, exist_ok=True)

    # 'data' 폴더 안에 'OBO.npy' 파일로 저장
    np.save(os.path.join(data_dir, 'Data'), simulation_list)

def resultClear():
    global Stats_PKT_TX_Trial
    global Stats_PKT_Success
    global Stats_PKT_Collision
    global Stats_PKT_Delay
    global Stats_RU_TX_Trial
    global Stats_RU_Idle
    global Stats_RU_Success
    global Stats_RU_Collision

    Stats_PKT_TX_Trial = 0
    Stats_PKT_Success = 0
    Stats_PKT_Collision = 0
    Stats_PKT_Delay = 0
    Stats_RU_TX_Trial = 0
    Stats_RU_Idle = 0
    Stats_RU_Success = 0
    Stats_RU_Collision = 0

# def distribute_all_items_to_clusters(arr, m):
#     clusters = [[] for _ in range(m)]  # 클러스터를 저장할 리스트
#     item_counts = [0] * m  # 각 클러스터에 들어간 값의 개수를 추적
#
#     for item in arr:
#         # 현재 클러스터 중 합이 가장 작은 클러스터에 원소 추가
#         min_sum_cluster = min(clusters, key=lambda cluster: sum(cluster))
#         min_sum_cluster.append(item)
#         cluster_index = clusters.index(min_sum_cluster)
#         item_counts[cluster_index] += 1
#
#     return clusters, item_counts

def distribute_all_items_to_clusters(arr, m):
    clusters = [[] for _ in range(m)]  # 클러스터를 저장할 리스트
    item_counts = [0] * m  # 각 클러스터에 들어간 값의 개수를 추적

    # 데이터를 균등하게 분배하기 위한 기준 개수 계산
    target_count = len(arr) // m

    for item in arr:
        # 현재 클러스터 중 합이 가장 작은 클러스터에 원소 추가
        min_sum_cluster = min(clusters, key=lambda cluster: sum(cluster))
        min_sum_cluster.append(item)
        cluster_index = clusters.index(min_sum_cluster)
        item_counts[cluster_index] += 1

        # 기준 개수에 도달하면 다른 클러스터에 할당하기 위해 현재 클러스터를 비워줌
        if item_counts[cluster_index] == target_count:
            clusters[cluster_index] = []

    return clusters, item_counts



# def main():
#     global USER_MAX
#     global current_User
#     USER_MAX = 100
#     for i in range(1, USER_MAX + 1):
#         print("======" + str(i) + "번" + "======")
#         current_User = i
#         resultClear()
#
#         # 랜덤 배열 생성
#         arr_length = random.randint(1, 100)
#         arr = [random.randint(0, 100) for _ in range(arr_length)]
#
#         # 클러스터 개수 입력
#         m = int(input("클러스터 개수를 입력하세요: "))
#
#         # 클러스터 할당 (적용하지 않은 경우)
#         clusters_no_cluster = [arr]
#         item_counts_no_cluster = [len(arr)]
#
#         # 클러스터 할당 결과 출력 (적용하지 않은 경우)
#         print("클러스터 할당 (적용하지 않은 경우) 결과:")
#         for i, (cluster, count) in enumerate(zip(clusters_no_cluster, item_counts_no_cluster)):
#             cluster_sum = sum(cluster)
#             print(f"클러스터 {i + 1}: {cluster} (클러스터 합계: {cluster_sum}, 값의 개수: {count})")
#
#         # 시뮬레이션 수행 (적용하지 않은 경우)
#         for k in range(0, NUM_SIM):
#             stationList.clear()
#             createSTA(i)
#             for j in range(0, NUM_DTI):
#                 incTrial()
#                 allocationRA_RU()
#                 checkCollision()
#                 addStats()
#                 changeStaVariables()
#         print("적용하지 않은 경우의 성능:")
#         print_Performance()
#
#         # 클러스터 할당 (적용한 경우)
#         clusters_with_cluster, item_counts_with_cluster = distribute_all_items_to_clusters(arr, m)
#
#         # 클러스터 할당 결과 출력 (적용한 경우)
#         print("\n클러스터 할당 (적용한 경우) 결과:")
#         for i, (cluster, count) in enumerate(zip(clusters_with_cluster, item_counts_with_cluster)):
#             cluster_sum = sum(cluster)
#             print(f"클러스터 {i + 1}: {cluster} (클러스터 합계: {cluster_sum}, 값의 개수: {count})")
#
#         # 시뮬레이션 수행 (적용한 경우)
#         for k in range(0, NUM_SIM):
#             stationList.clear()
#             createSTA(i)
#             for j in range(0, NUM_DTI):
#                 incTrial()
#                 allocationRA_RU()
#                 checkCollision()
#                 addStats()
#                 changeStaVariables()
#         print("\n적용한 경우의 성능:")
#         print_Performance()
#
#         save()
#
# main()
# def main():
#     global USER_MAX
#     global current_User
#     USER_MAX = 100
#     for i in range(1, USER_MAX + 1):
#         print("======" + str(i) + "번" + "======")
#         current_User = i
#         resultClear()
#
#         # 랜덤 배열 생성
#         arr_length = random.randint(1, 100)
#         arr = [random.randint(0, 100) for _ in range(arr_length)]
#
#         # 클러스터 개수 입력
#         m = int(input("클러스터 개수를 입력하세요: "))
#
#         # 클러스터 할당 (적용하지 않은 경우)
#         clusters_no_cluster, item_counts_no_cluster = distribute_all_items_to_clusters(arr, m)
#
#         # 클러스터 할당 결과 출력 (적용하지 않은 경우)
#         print("클러스터 할당 (적용하지 않은 경우) 결과:")
#         for i, (cluster, count) in enumerate(zip(clusters_no_cluster, item_counts_no_cluster)):
#             cluster_sum = sum(cluster)
#             print(f"클러스터 {i + 1}: {cluster} (클러스터 합계: {cluster_sum}, 값의 개수: {count})")
#
#         # 시뮬레이션 수행 (적용하지 않은 경우)
#         for k in range(0, NUM_SIM):
#             stationList.clear()
#             createSTA(i)
#             for j in range(0, NUM_DTI):
#                 incTrial()
#                 allocationRA_RU()
#                 checkCollision()
#                 addStats()
#                 changeStaVariables()
#         print("적용하지 않은 경우의 성능:")
#         print_Performance()
#
#         # 클러스터 할당 (적용한 경우)
#         clusters_with_cluster, item_counts_with_cluster = distribute_all_items_to_clusters(arr, m)
#
#         # 클러스터 할당 결과 출력 (적용한 경우)
#         print("\n클러스터 할당 (적용한 경우) 결과:")
#         for i, (cluster, count) in enumerate(zip(clusters_with_cluster, item_counts_with_cluster)):
#             cluster_sum = sum(cluster)
#             print(f"클러스터 {i + 1}: {cluster} (클러스터 합계: {cluster_sum}, 값의 개수: {count})")
#
#         # 시뮬레이션 수행 (적용한 경우)
#         for k in range(0, NUM_SIM):
#             stationList.clear()
#             createSTA(i)
#             for j in range(0, NUM_DTI):
#                 incTrial()
#                 allocationRA_RU()
#                 checkCollision()
#                 addStats()
#                 changeStaVariables()
#         print("\n적용한 경우의 성능:")
#         print_Performance()
#
#         save()
#
# main()
def main():
    global USER_MAX
    global current_User
    USER_MAX = 100
    for i in range(1, USER_MAX + 1):
        print("======" + str(i) + "번" + "======")
        current_User = i
        resultClear()

        # 랜덤 배열 생성
        arr_length = random.randint(1, 100)
        arr = [random.randint(0, 100) for _ in range(arr_length)]

        # 클러스터 개수 입력
        m = int(input("클러스터 개수를 입력하세요: "))

        # 클러스터 할당 (적용하지 않은 경우)
        clusters_no_cluster = [arr]
        item_counts_no_cluster = [len(arr)]

        # 클러스터 할당 결과 출력 (적용하지 않은 경우)
        print("클러스터 할당 (적용하지 않은 경우) 결과:")
        for i, (cluster, count) in enumerate(zip(clusters_no_cluster, item_counts_no_cluster)):
            cluster_sum = sum(cluster)
            print(f"클러스터 {i + 1}: {cluster} (클러스터 합계: {cluster_sum}, 값의 개수: {count})")

        # 시뮬레이션 수행 (적용하지 않은 경우)
        for k in range(0, NUM_SIM):
            stationList.clear()
            createSTA(current_User)
            for j in range(0, NUM_DTI):
                incTrial()
                allocationRA_RU()
                checkCollision()
                addStats()
                changeStaVariables()
        print("적용하지 않은 경우의 성능:")
        print_Performance()

        # 클러스터 할당 (적용한 경우)
        clusters_with_cluster, item_counts_with_cluster = distribute_all_items_to_clusters(arr, m)

        # 클러스터 할당 결과 출력 (적용한 경우)
        print("\n클러스터 할당 (적용한 경우) 결과:")
        for i, (cluster, count) in enumerate(zip(clusters_with_cluster, item_counts_with_cluster)):
            cluster_sum = sum(cluster)
            print(f"클러스터 {i + 1}: {cluster} (클러스터 합계: {cluster_sum}, 값의 개수: {count})")

        # 시뮬레이션 수행 (적용한 경우)
        for k in range(0, NUM_SIM):
            stationList.clear()
            createSTA(current_User)
            for j in range(0, NUM_DTI):
                incTrial()
                allocationRA_RU()
                checkCollision()
                addStats()
                changeStaVariables()
        print("\n적용한 경우의 성능:")
        print_Performance()

        save()

main()
