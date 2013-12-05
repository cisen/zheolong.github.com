#coding=utf-8
"""
下过象棋的人都知道，马只能走'日'字形（包括旋转90°的日），现在想象一下，给你一个n行m列网格棋盘，
棋盘的左下角有一匹马，请你计算至少需要几步可以将它移动到棋盘的右上角，若无法走到，则输出-1.
如n=1，m=2,则至少需要1步；若n=1，m=3,则输出-1。
"""

"""
棋盘坐标：行 0...n 列 0...m
搜索方向：从一个点周围的八个方向（有的点如接近边界的点可选的方向较少）中除去之前搜索过的方向(需要辅助flag矩阵)；如果走到某个点以后，该点周围的可选方向都已经搜索过了，那么返回-1，表示从该点到左下角不可达；把一个点周围返回非-1的点的值比较取最小，就是该点到左下角步数（如果从右上方开始搜索的话）
"""

n=1
m=3
n+=1
m+=1
flag_visit = [([False]*m) for i in range(n)]
print flag_visit
direction = [(-2,-1),(-2,1),(2,-1),(2,1),(-1,-2),(-1,2),(1,-2),(1,2)]


def dfs(flag_visit,i,j,n,m):
	if i<0 or j<0 or i>=n or j>=m:
		#越界了，返回-1
		return -1
	if i==0 and j==0:
		#访问到了，返回0，因为该点就是左下角节点，所以距离是0
		return 0
	if flag_visit[i][j]:
		#访问过了，返回-1
		return -1
	min_step = -1
	for k in range(len(direction)):
		x,y=direction[k]
		flag_visit[i][j] = True
		
		t = dfs(flag_visit,i+x,j+y,n,m)
		#如果t不是-1，表示可用
		if t!=-1:
			#要计算i,j点到0,0点的距离，就需要将t+1，因为t是周围点到0,0的距离
			t+=1
			if min_step==-1: #如果现在min_step还是-1，意味着还没有遇到可行点
				min_step = t
			else:  #否则，就需要取各个可行点中距离0,0最近的那个了
				min_step = min(min_step,t)
	return min_step

print dfs(flag_visit,n-1,m-1,n,m)
