import React, { useState, useEffect, useRef, useMemo, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import ForceGraph2D from 'react-force-graph-2d'
import {
  Search,
  Plus,
  Minus,
  Maximize2,
  Share2,
  X,
  ExternalLink,
  ChevronLeft,
  ChevronRight
} from 'lucide-react'
import { api } from '../api/client'

interface SemanticNode {
  id: string
  label: string
  type: 'topic' | 'category' | 'entity'
  document_count: number
  connection_count: number
  sentiment: {
    negative: number
    neutral: number
    positive: number
  }
  x?: number
  y?: number
}

interface SemanticEdge {
  id: string
  source: any
  target: any
  weight: number
}

interface LineageNode {
  id: string
  model_id?: string
  label: string
  name?: string
  type: 'user' | 'dataset' | 'model' | 'prediction' | 'feedback'
  email?: string
  role?: string
  row_count?: number
  source?: string
  algorithm?: string
  feature_type?: string
  status?: string
  deployed?: boolean
  f1?: number | null
  accuracy?: number | null
  precision?: number | null
  recall?: number | null
  created_by?: string
  trained_on?: string
  count?: number
  created_at?: string
  x?: number
  y?: number
}

interface LineageEdge {
  id: string
  source: any
  target: any
  type: string
  label: string
}

export const InsightGraph: React.FC = () => {
  const navigate = useNavigate()
  const fgRef = useRef<any>(null)
  const containerRef = useRef<HTMLDivElement>(null)

  const [activeTab, setActiveTab] = useState<'semantic' | 'lineage'>('semantic')
  const [selectedDatasetId, setSelectedDatasetId] = useState<string>('')
  const [searchQuery, setSearchQuery] = useState('')
  const [isPhysicsPaused, setIsPhysicsPaused] = useState(false)
  const [dimensions, setDimensions] = useState({ width: 800, height: 600 })

  const [semanticFilters, setSemanticFilters] = useState({
    topic: true,
    category: true,
    entity: true
  })

  const [lineageFilters, setLineageFilters] = useState({
    user: true,
    dataset: true,
    model: true,
    prediction: true,
    feedback: true
  })

  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null)
  const [hoveredNode, setHoveredNode] = useState<any | null>(null)
  const [cursorPos, setCursorPos] = useState({ x: 0, y: 0 })

  const [isDocModalOpen, setIsDocModalOpen] = useState(false)
  const [docPage, setDocPage] = useState(1)

  const { data: datasets } = useQuery({
    queryKey: ['datasetsList'],
    queryFn: async () => {
      const list = await api.datasets.list()
      if (list.length > 0 && !selectedDatasetId) {
        setSelectedDatasetId(list[0].id)
      }
      return list
    }
  })

  const { data: semanticData, isLoading: isSemanticLoading, isError: isSemanticError } = useQuery({
    queryKey: ['semanticGraph', selectedDatasetId],
    queryFn: () => api.graph.semantic(selectedDatasetId || undefined),
    enabled: activeTab === 'semantic'
  })

  const { data: lineageData, isLoading: isLineageLoading, isError: isLineageError } = useQuery({
    queryKey: ['lineageGraph'],
    queryFn: () => api.graph.lineage(),
    enabled: activeTab === 'lineage'
  })

  const { data: nodeDocsData, isLoading: isNodeDocsLoading } = useQuery({
    queryKey: ['nodeDocuments', selectedNodeId, docPage, selectedDatasetId],
    queryFn: () => {
      if (!selectedNodeId) return null
      return api.graph.nodeDocuments(selectedNodeId, docPage, 8, selectedDatasetId || undefined)
    },
    enabled: isDocModalOpen && !!selectedNodeId && activeTab === 'semantic'
  })

  useEffect(() => {
    const updateDimensions = () => {
      if (containerRef.current) {
        const { clientWidth, clientHeight } = containerRef.current
        setDimensions({
          width: clientWidth || 800,
          height: clientHeight || 600
        })
      }
    }
    updateDimensions()
    window.addEventListener('resize', updateDimensions)
    return () => window.removeEventListener('resize', updateDimensions)
  }, [])

  useEffect(() => {
    setSelectedNodeId(null)
    setHoveredNode(null)
  }, [activeTab, selectedDatasetId])

  const filteredSemanticGraph = useMemo(() => {
    if (!semanticData || !semanticData.nodes) {
      return { nodes: [], edges: [] }
    }
    const filteredNodes = semanticData.nodes.filter((node: SemanticNode) => {
      if (!semanticFilters[node.type]) return false
      if (searchQuery.trim()) {
        return node.label.toLowerCase().includes(searchQuery.toLowerCase())
      }
      return true
    })
    const nodeSet = new Set(filteredNodes.map((n: SemanticNode) => n.id))
    const filteredEdges = (semanticData.edges || []).filter((edge: SemanticEdge) => {
      const srcId = typeof edge.source === 'object' ? edge.source.id : edge.source
      const tgtId = typeof edge.target === 'object' ? edge.target.id : edge.target
      return nodeSet.has(srcId) && nodeSet.has(tgtId)
    })
    return { nodes: filteredNodes, edges: filteredEdges }
  }, [semanticData, semanticFilters, searchQuery])

  const filteredLineageGraph = useMemo(() => {
    if (!lineageData || !lineageData.nodes) {
      return { nodes: [], edges: [] }
    }
    const filteredNodes = lineageData.nodes.filter((node: LineageNode) => {
      if (!lineageFilters[node.type]) return false
      if (searchQuery.trim()) {
        const nameMatch = node.name && node.name.toLowerCase().includes(searchQuery.toLowerCase())
        const labelMatch = node.label && node.label.toLowerCase().includes(searchQuery.toLowerCase())
        return nameMatch || labelMatch
      }
      return true
    })
    const nodeSet = new Set(filteredNodes.map((n: LineageNode) => n.id))
    const filteredEdges = (lineageData.edges || []).filter((edge: LineageEdge) => {
      const srcId = typeof edge.source === 'object' ? edge.source.id : edge.source
      const tgtId = typeof edge.target === 'object' ? edge.target.id : edge.target
      return nodeSet.has(srcId) && nodeSet.has(tgtId)
    })
    return { nodes: filteredNodes, edges: filteredEdges }
  }, [lineageData, lineageFilters, searchQuery])

  const selectedNode = useMemo(() => {
    if (!selectedNodeId) return null
    if (activeTab === 'semantic') {
      return semanticData?.nodes?.find((n: SemanticNode) => n.id === selectedNodeId) || null
    }
    return lineageData?.nodes?.find((n: LineageNode) => n.id === selectedNodeId) || null
  }, [selectedNodeId, activeTab, semanticData, lineageData])

  const connectedSemanticNeighbors = useMemo(() => {
    if (!selectedNodeId || activeTab !== 'semantic' || !semanticData) return []
    const neighborsMap = new Map<string, number>()
    ;(semanticData.edges || []).forEach((edge: SemanticEdge) => {
      const srcId = typeof edge.source === 'object' ? edge.source.id : edge.source
      const tgtId = typeof edge.target === 'object' ? edge.target.id : edge.target
      if (srcId === selectedNodeId) {
        neighborsMap.set(tgtId, Math.max(neighborsMap.get(tgtId) || 0, edge.weight))
      } else if (tgtId === selectedNodeId) {
        neighborsMap.set(srcId, Math.max(neighborsMap.get(srcId) || 0, edge.weight))
      }
    })
    const result: Array<{ node: SemanticNode; sharedDocs: number }> = []
    neighborsMap.forEach((weight, nid) => {
      const n = semanticData.nodes.find((item: SemanticNode) => item.id === nid)
      if (n) {
        result.push({ node: n, sharedDocs: weight })
      }
    })
    result.sort((a, b) => b.sharedDocs - a.sharedDocs)
    return result
  }, [selectedNodeId, activeTab, semanticData])

  const selectedNeighborIds = useMemo(() => {
    return new Set(connectedSemanticNeighbors.map((item) => item.node.id))
  }, [connectedSemanticNeighbors])

  const handleZoomIn = () => {
    if (fgRef.current) {
      fgRef.current.zoom(fgRef.current.zoom() * 1.3, 300)
    }
  }

  const handleZoomOut = () => {
    if (fgRef.current) {
      fgRef.current.zoom(fgRef.current.zoom() / 1.3, 300)
    }
  }

  const handleFitScreen = () => {
    if (fgRef.current) {
      fgRef.current.zoomToFit(400, 40)
    }
  }

  const togglePhysics = () => {
    setIsPhysicsPaused((prev) => {
      const next = !prev
      if (fgRef.current) {
        if (next) {
          fgRef.current.pauseAnimation()
        } else {
          fgRef.current.resumeAnimation()
        }
      }
      return next
    })
  }

  const handleNodeClick = useCallback((node: any) => {
    setSelectedNodeId((prev) => (prev === node.id ? null : node.id))
    if (fgRef.current && node.x !== undefined && node.y !== undefined) {
      fgRef.current.centerAt(node.x, node.y, 400)
    }
  }, [])

  const handleCanvasMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    const rect = e.currentTarget.getBoundingClientRect()
    setCursorPos({
      x: e.clientX - rect.left,
      y: e.clientY - rect.top
    })
  }

  const paintSemanticNode = useCallback(
    (node: any, ctx: CanvasRenderingContext2D, globalScale: number) => {
      const isSelected = selectedNodeId === node.id
      const isNeighbor = selectedNodeId ? selectedNeighborIds.has(node.id) : false
      const isDimmed = selectedNodeId ? !isSelected && !isNeighbor : false

      ctx.save()
      ctx.globalAlpha = isDimmed ? 0.15 : 1.0

      const docCount = node.document_count || 1
      const radius = Math.max(5, Math.min(22, 6 + Math.sqrt(docCount) * 1.3))

      let fillColor = '#4f46e5'
      if (node.type === 'category') fillColor = '#10b981'
      if (node.type === 'entity') fillColor = '#f59e0b'

      if (isSelected) {
        ctx.beginPath()
        ctx.arc(node.x, node.y, radius + 4, 0, 2 * Math.PI, false)
        ctx.strokeStyle = '#818cf8'
        ctx.lineWidth = 2.5
        ctx.stroke()
      }

      ctx.beginPath()
      ctx.arc(node.x, node.y, radius, 0, 2 * Math.PI, false)
      ctx.fillStyle = fillColor
      ctx.fill()

      if (globalScale > 0.7 || isSelected || isNeighbor) {
        const fontSize = Math.max(10, Math.min(14, 11 / globalScale))
        ctx.font = `${fontSize}px Inter, sans-serif`
        ctx.textAlign = 'center'
        ctx.textBaseline = 'top'
        ctx.fillStyle = isSelected ? '#ffffff' : '#94a3b8'
        ctx.fillText(node.label, node.x, node.y + radius + 4)
      }

      ctx.restore()
    },
    [selectedNodeId, selectedNeighborIds]
  )

  const paintLineageNode = useCallback(
    (node: any, ctx: CanvasRenderingContext2D) => {
      const isSelected = selectedNodeId === node.id
      ctx.save()

      if (node.type === 'user') {
        const radius = 14
        ctx.beginPath()
        ctx.arc(node.x, node.y, radius, 0, 2 * Math.PI)
        ctx.fillStyle = '#4f6bf5'
        ctx.fill()
        if (isSelected) {
          ctx.strokeStyle = '#93c5fd'
          ctx.lineWidth = 2.5
          ctx.stroke()
        }
        ctx.font = '11px Inter, sans-serif'
        ctx.textAlign = 'center'
        ctx.fillStyle = '#e2e8f0'
        ctx.fillText(node.label, node.x, node.y + radius + 4)
      } else if (node.type === 'dataset') {
        const width = 110
        const height = 36
        const x = node.x - width / 2
        const y = node.y - height / 2
        ctx.beginPath()
        ctx.roundRect(x, y, width, height, 8)
        ctx.fillStyle = '#132c22'
        ctx.fill()
        ctx.strokeStyle = isSelected ? '#6ee7b7' : '#10b981'
        ctx.lineWidth = isSelected ? 2 : 1.2
        ctx.stroke()

        ctx.font = 'bold 11px Inter, sans-serif'
        ctx.textAlign = 'center'
        ctx.fillStyle = '#ffffff'
        const labelText = node.label.length > 14 ? node.label.slice(0, 13) + '...' : node.label
        ctx.fillText(labelText, node.x, y + 13)

        ctx.font = '10px Inter, sans-serif'
        ctx.fillStyle = '#6ee7b7'
        ctx.fillText(`${(node.row_count || 0).toLocaleString()} rows`, node.x, y + 27)
      } else if (node.type === 'model') {
        const radius = 22
        if (node.deployed) {
          ctx.beginPath()
          ctx.arc(node.x, node.y, radius + 12, 0, 2 * Math.PI)
          ctx.fillStyle = 'rgba(99, 102, 241, 0.16)'
          ctx.fill()

          ctx.beginPath()
          ctx.arc(node.x, node.y, radius + 6, 0, 2 * Math.PI)
          ctx.fillStyle = 'rgba(99, 102, 241, 0.28)'
          ctx.fill()
        }

        ctx.beginPath()
        for (let i = 0; i < 6; i++) {
          const angle = (Math.PI / 3) * i
          const hx = node.x + radius * Math.cos(angle)
          const hy = node.y + radius * Math.sin(angle)
          if (i === 0) ctx.moveTo(hx, hy)
          else ctx.lineTo(hx, hy)
        }
        ctx.closePath()
        ctx.fillStyle = '#1e244a'
        ctx.fill()
        ctx.strokeStyle = isSelected ? '#a5b4fc' : '#6366f1'
        ctx.lineWidth = isSelected ? 2.5 : 1.5
        ctx.stroke()

        ctx.font = 'bold 12px Inter, sans-serif'
        ctx.textAlign = 'center'
        ctx.textBaseline = 'middle'
        ctx.fillStyle = '#ffffff'
        ctx.fillText(node.label, node.x, node.y)

        ctx.font = '11px Inter, sans-serif'
        ctx.textAlign = 'center'
        ctx.textBaseline = 'top'
        ctx.fillStyle = node.deployed ? '#818cf8' : '#94a3b8'
        ctx.fillText(
          `${node.name || 'Model'}${node.deployed ? ' · Deployed' : ''}`,
          node.x,
          node.y + radius + 6
        )
      } else if (node.type === 'prediction') {
        const width = 110
        const height = 36
        const x = node.x - width / 2
        const y = node.y - height / 2
        ctx.beginPath()
        ctx.roundRect(x, y, width, height, 18)
        ctx.fillStyle = '#262017'
        ctx.fill()
        ctx.strokeStyle = isSelected ? '#fde68a' : '#f59e0b'
        ctx.lineWidth = isSelected ? 2 : 1.2
        ctx.stroke()

        const lines = node.label.split('\n')
        ctx.font = 'bold 10px Inter, sans-serif'
        ctx.textAlign = 'center'
        ctx.fillStyle = '#ffffff'
        ctx.fillText(lines[0] || '', node.x, y + 13)

        if (lines[1]) {
          ctx.font = '10px Inter, sans-serif'
          ctx.fillStyle = '#fbbf24'
          ctx.fillText(lines[1], node.x, y + 26)
        }
      } else if (node.type === 'feedback') {
        const width = 100
        const height = 36
        const x = node.x - width / 2
        const y = node.y - height / 2
        ctx.beginPath()
        ctx.roundRect(x, y, width, height, 6)
        ctx.fillStyle = '#2d181c'
        ctx.fill()
        ctx.strokeStyle = isSelected ? '#fca5a5' : '#ef4444'
        ctx.lineWidth = isSelected ? 2 : 1.2
        ctx.stroke()

        const lines = node.label.split('\n')
        ctx.font = 'bold 10px Inter, sans-serif'
        ctx.textAlign = 'center'
        ctx.fillStyle = '#ffffff'
        ctx.fillText(lines[0] || 'Corrections', node.x, y + 13)

        if (lines[1]) {
          ctx.font = '10px Inter, sans-serif'
          ctx.fillStyle = '#f87171'
          ctx.fillText(lines[1], node.x, y + 26)
        }
      }

      ctx.restore()
    },
    [selectedNodeId]
  )

  const paintLineageLink = useCallback(
    (link: any, ctx: CanvasRenderingContext2D) => {
      const src = link.source
      const tgt = link.target
      if (!src || !tgt || src.x === undefined || tgt.x === undefined) return
      const midX = (src.x + tgt.x) / 2
      const midY = (src.y + tgt.y) / 2

      ctx.save()
      ctx.font = '9px Inter, sans-serif'
      ctx.textAlign = 'center'
      ctx.textBaseline = 'middle'

      const text = link.label || ''
      const textWidth = ctx.measureText(text).width

      ctx.fillStyle = '#151821'
      ctx.fillRect(midX - textWidth / 2 - 4, midY - 7, textWidth + 8, 14)

      ctx.fillStyle = '#94a3b8'
      ctx.fillText(text, midX, midY)
      ctx.restore()
    },
    []
  )

  const currentGraphData = activeTab === 'semantic' ? filteredSemanticGraph : filteredLineageGraph
  const isCurrentEmpty = currentGraphData.nodes.length === 0
  const isCurrentLoading = activeTab === 'semantic' ? isSemanticLoading : isLineageLoading
  const isCurrentError = activeTab === 'semantic' ? isSemanticError : isLineageError

  return (
    <div className="flex flex-col gap-4 h-full max-w-[1600px] mx-auto pb-4">
      <div>
        <p className="text-xs text-slate-400">
          {activeTab === 'semantic'
            ? 'Shows how topics, categories and entities connect across your analyzed customer feedback.'
            : 'Shows how users, datasets, model versions, predictions and feedback relate.'}
        </p>
      </div>

      <div className="flex items-center gap-8 border-b border-[#212635]">
        <button
          onClick={() => setActiveTab('semantic')}
          className={`pb-3 text-sm font-medium transition-colors relative ${
            activeTab === 'semantic' ? 'text-white' : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          Semantic Network
          {activeTab === 'semantic' && (
            <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-[#4f6bf5] rounded-full" />
          )}
        </button>
        <button
          onClick={() => setActiveTab('lineage')}
          className={`pb-3 text-sm font-medium transition-colors relative ${
            activeTab === 'lineage' ? 'text-white' : 'text-slate-400 hover:text-slate-200'
          }`}
        >
          System Lineage
          {activeTab === 'lineage' && (
            <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-[#4f6bf5] rounded-full" />
          )}
        </button>
      </div>

      <div className="flex items-center justify-between gap-4 flex-wrap">
        <div className="flex items-center gap-3 flex-wrap">
          <select
            value={activeTab === 'semantic' ? selectedDatasetId : 'all'}
            onChange={(e) => {
              if (activeTab === 'semantic') {
                setSelectedDatasetId(e.target.value)
              }
            }}
            disabled={activeTab === 'lineage'}
            className="px-3.5 py-1.5 text-xs bg-[#191c25] border border-[#252a36] rounded-lg text-slate-200 focus:outline-none focus:border-[#4f6bf5] min-w-[180px] disabled:opacity-70"
          >
            {activeTab === 'semantic' ? (
              (datasets || []).map((d: any) => (
                <option key={d.id} value={d.id}>
                  {d.name}
                </option>
              ))
            ) : (
              <option value="all">All datasets</option>
            )}
          </select>

          <div className="relative">
            <Search size={14} className="absolute left-3 top-2.5 text-slate-500" />
            <input
              type="text"
              placeholder="Find a node"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-8 pr-3.5 py-1.5 text-xs bg-[#191c25] border border-[#252a36] rounded-lg text-slate-200 placeholder-slate-500 focus:outline-none focus:border-[#4f6bf5] w-48"
            />
          </div>

          {activeTab === 'semantic' ? (
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={() => setSemanticFilters((f) => ({ ...f, topic: !f.topic }))}
                className={`flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium border transition-colors ${
                  semanticFilters.topic
                    ? 'bg-[#1e2442] text-[#818cf8] border-[#374174]'
                    : 'bg-[#151821] text-slate-500 border-[#252a36]'
                }`}
              >
                <span className="w-2 h-2 rounded-full bg-[#4f46e5]" />
                <span>Topics</span>
              </button>
              <button
                type="button"
                onClick={() => setSemanticFilters((f) => ({ ...f, category: !f.category }))}
                className={`flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium border transition-colors ${
                  semanticFilters.category
                    ? 'bg-[#132c22] text-[#34d399] border-[#1b4332]'
                    : 'bg-[#151821] text-slate-500 border-[#252a36]'
                }`}
              >
                <span className="w-2 h-2 rounded-full bg-[#10b981]" />
                <span>Categories</span>
              </button>
              <button
                type="button"
                onClick={() => setSemanticFilters((f) => ({ ...f, entity: !f.entity }))}
                className={`flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium border transition-colors ${
                  semanticFilters.entity
                    ? 'bg-[#332712] text-[#fbbf24] border-[#523e1b]'
                    : 'bg-[#151821] text-slate-500 border-[#252a36]'
                }`}
              >
                <span className="w-2 h-2 rounded-full bg-[#f59e0b]" />
                <span>Entities</span>
              </button>
            </div>
          ) : (
            <div className="flex items-center gap-2 flex-wrap">
              <button
                type="button"
                onClick={() => setLineageFilters((f) => ({ ...f, user: !f.user }))}
                className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border transition-colors ${
                  lineageFilters.user
                    ? 'bg-[#1c2438] text-[#93c5fd] border-[#2b3a5d]'
                    : 'bg-[#151821] text-slate-500 border-[#252a36]'
                }`}
              >
                <span className="w-2 h-2 rounded-full bg-[#3b82f6]" />
                <span>Users</span>
              </button>
              <button
                type="button"
                onClick={() => setLineageFilters((f) => ({ ...f, dataset: !f.dataset }))}
                className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border transition-colors ${
                  lineageFilters.dataset
                    ? 'bg-[#132c22] text-[#34d399] border-[#1b4332]'
                    : 'bg-[#151821] text-slate-500 border-[#252a36]'
                }`}
              >
                <span className="w-2 h-2 rounded-sm bg-[#10b981]" />
                <span>Datasets</span>
              </button>
              <button
                type="button"
                onClick={() => setLineageFilters((f) => ({ ...f, model: !f.model }))}
                className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border transition-colors ${
                  lineageFilters.model
                    ? 'bg-[#1e2442] text-[#818cf8] border-[#374174]'
                    : 'bg-[#151821] text-slate-500 border-[#252a36]'
                }`}
              >
                <span className="w-2 h-2 rounded-full bg-[#6366f1]" />
                <span>Models</span>
              </button>
              <button
                type="button"
                onClick={() => setLineageFilters((f) => ({ ...f, prediction: !f.prediction }))}
                className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border transition-colors ${
                  lineageFilters.prediction
                    ? 'bg-[#332712] text-[#fbbf24] border-[#523e1b]'
                    : 'bg-[#151821] text-slate-500 border-[#252a36]'
                }`}
              >
                <span className="w-2 h-2 rounded-full bg-[#f59e0b]" />
                <span>Predictions</span>
              </button>
              <button
                type="button"
                onClick={() => setLineageFilters((f) => ({ ...f, feedback: !f.feedback }))}
                className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border transition-colors ${
                  lineageFilters.feedback
                    ? 'bg-[#33181b] text-[#f87171] border-[#53262b]'
                    : 'bg-[#151821] text-slate-500 border-[#252a36]'
                }`}
              >
                <span className="w-2 h-2 rounded-sm bg-[#ef4444]" />
                <span>Feedback</span>
              </button>
            </div>
          )}
        </div>

        <div className="flex items-center gap-2">
          <div className="flex items-center border border-[#252a36] rounded-lg bg-[#191c25] overflow-hidden">
            <button
              onClick={handleZoomIn}
              className="p-1.5 text-slate-300 hover:text-white hover:bg-[#252a36] transition-colors"
              title="Zoom in"
            >
              <Plus size={15} />
            </button>
            <div className="w-[1px] h-4 bg-[#252a36]" />
            <button
              onClick={handleZoomOut}
              className="p-1.5 text-slate-300 hover:text-white hover:bg-[#252a36] transition-colors"
              title="Zoom out"
            >
              <Minus size={15} />
            </button>
            <div className="w-[1px] h-4 bg-[#252a36]" />
            <button
              onClick={handleFitScreen}
              className="p-1.5 text-slate-300 hover:text-white hover:bg-[#252a36] transition-colors"
              title="Fit to screen"
            >
              <Maximize2 size={15} />
            </button>
          </div>

          <button
            onClick={togglePhysics}
            className="flex items-center gap-2 px-3 py-1.5 bg-[#191c25] border border-[#252a36] rounded-lg text-xs text-slate-300 hover:text-white transition-colors"
          >
            <div
              className={`w-3.5 h-3.5 rounded-full transition-colors ${
                isPhysicsPaused ? 'bg-[#f59e0b]' : 'bg-[#10b981]'
              }`}
            />
            <span>Pause physics</span>
          </button>
        </div>
      </div>

      <div className="flex gap-5 flex-1 min-h-[580px]">
        <div
          ref={containerRef}
          onMouseMove={handleCanvasMouseMove}
          className="relative flex-1 bg-[#141720] rounded-xl border border-[#212635] overflow-hidden"
          style={{
            backgroundImage: 'radial-gradient(circle, #222736 1px, transparent 1px)',
            backgroundSize: '24px 24px'
          }}
        >
          {isCurrentLoading ? (
            <div className="absolute inset-0 flex items-center justify-center bg-[#141720]/80 z-20">
              <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-[#4f6bf5]"></div>
            </div>
          ) : isCurrentError ? (
            <div className="absolute inset-0 flex flex-col items-center justify-center p-8 text-center z-20">
              <h3 className="text-sm font-semibold text-rose-400 mb-1">Failed to load graph</h3>
              <p className="text-xs text-slate-400">Ensure semantic analysis has run for this dataset.</p>
            </div>
          ) : isCurrentEmpty ? (
            <div className="absolute inset-0 flex items-center justify-center p-6 z-20">
              <div className="bg-[#191c25] border border-[#252a36] rounded-2xl p-8 max-w-md text-center flex flex-col items-center shadow-2xl">
                <div className="w-12 h-12 rounded-xl bg-[#202538] flex items-center justify-center text-[#818cf8] mb-4">
                  <Share2 size={24} />
                </div>
                <h3 className="text-base font-semibold text-white mb-2">No graph yet</h3>
                <p className="text-xs text-slate-400 mb-6 leading-relaxed">
                  The graph appears after data is analyzed. Run a semantic analysis on a dataset to see how
                  topics, categories and entities connect.
                </p>
                <button
                  onClick={() => navigate('/analysis')}
                  className="px-5 py-2.5 bg-[#4f6bf5] hover:bg-[#4159d4] text-white text-xs font-medium rounded-lg transition-colors"
                >
                  Go to Semantic Analysis
                </button>
              </div>
            </div>
          ) : null}

          {!isCurrentEmpty && !isCurrentLoading && (
            <ForceGraph2D
              ref={fgRef}
              width={dimensions.width}
              height={dimensions.height}
              graphData={{ nodes: currentGraphData.nodes, links: currentGraphData.edges }}
              nodeId="id"
              nodeCanvasObject={activeTab === 'semantic' ? paintSemanticNode : paintLineageNode}
              linkCanvasObject={activeTab === 'lineage' ? paintLineageLink : undefined}
              linkCanvasObjectMode={activeTab === 'lineage' ? () => 'after' : undefined}
              linkCurvature={activeTab === 'semantic' ? 0.15 : 0}
              linkWidth={(link: any) => {
                if (activeTab === 'semantic') {
                  return Math.max(1, Math.min(5, (link.weight || 1) * 0.5))
                }
                return 1.5
              }}
              linkColor={(link: any) => {
                if (activeTab === 'semantic') {
                  const srcId = typeof link.source === 'object' ? link.source.id : link.source
                  const tgtId = typeof link.target === 'object' ? link.target.id : link.target
                  if (selectedNodeId && (srcId === selectedNodeId || tgtId === selectedNodeId)) {
                    return '#6366f1'
                  }
                  return selectedNodeId ? 'rgba(75, 85, 99, 0.15)' : 'rgba(99, 102, 241, 0.25)'
                }
                return '#475569'
              }}
              onNodeClick={handleNodeClick}
              onNodeHover={(node) => setHoveredNode(node || null)}
              cooldownTicks={isPhysicsPaused ? 0 : 80}
              enableNodeDrag={!isPhysicsPaused}
            />
          )}

          {hoveredNode && activeTab === 'semantic' && (
            <div
              className="absolute z-30 pointer-events-none bg-[#191c25] border border-[#2b3347] rounded-lg p-3 shadow-xl text-xs max-w-xs"
              style={{
                left: Math.min(cursorPos.x + 12, dimensions.width - 200),
                top: Math.max(cursorPos.y - 60, 10)
              }}
            >
              <div className="font-semibold text-white">{hoveredNode.label}</div>
              <div className="text-slate-400 capitalize mt-0.5">
                {hoveredNode.type} · {(hoveredNode.document_count || 0).toLocaleString()} documents
              </div>
              {hoveredNode.sentiment && (
                <div className="text-[#f87171] font-medium mt-1">
                  {hoveredNode.sentiment.negative}% negative
                </div>
              )}
            </div>
          )}

          <div className="absolute bottom-3 left-4 bg-[#141720]/90 border border-[#252a36] rounded-lg px-4 py-2 flex items-center gap-4 text-[11px] text-slate-400 backdrop-blur-sm z-10">
            {activeTab === 'semantic' ? (
              <>
                <div className="flex items-center gap-1.5">
                  <span className="w-2 h-2 rounded-full bg-[#4f46e5]" />
                  <span>Topic</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <span className="w-2 h-2 rounded-full bg-[#10b981]" />
                  <span>Category</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <span className="w-2 h-2 rounded-full bg-[#f59e0b]" />
                  <span>Entity</span>
                </div>
                <span className="text-slate-600">·</span>
                <span>Size = documents · Edge width = shared documents</span>
              </>
            ) : (
              <>
                <div className="flex items-center gap-1.5">
                  <span className="w-2 h-2 rounded-full bg-[#3b82f6]" />
                  <span>User</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <span className="w-2 h-2 rounded-sm bg-[#10b981]" />
                  <span>Dataset</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <span className="w-2 h-2 rounded-full bg-[#6366f1]" />
                  <span>Model</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <span className="w-2 h-2 rounded-full bg-[#f59e0b]" />
                  <span>Prediction</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <span className="w-2 h-2 rounded-sm bg-[#ef4444]" />
                  <span>Feedback</span>
                </div>
                <span className="text-slate-600">·</span>
                <span>Glow = deployed model</span>
              </>
            )}
          </div>
        </div>

        <div className="w-80 flex-shrink-0 bg-[#161922] border border-[#252a36] rounded-xl p-5 flex flex-col justify-between overflow-y-auto">
          {activeTab === 'semantic' ? (
            !selectedNode ? (
              <div className="flex flex-col gap-2">
                <h3 className="text-sm font-semibold text-white">Details</h3>
                <p className="text-xs text-slate-400 leading-relaxed">
                  Select a node in the graph to see its type, document count, connections and sentiment.
                </p>
              </div>
            ) : (
              <div className="flex flex-col gap-5">
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <h3 className="text-base font-bold text-white tracking-tight">{selectedNode.label}</h3>
                  </div>
                  <span
                    className={`text-[11px] font-medium px-2.5 py-0.5 rounded-full capitalize border ${
                      selectedNode.type === 'topic'
                        ? 'bg-[#212442] text-[#818cf8] border-[#363a69]'
                        : selectedNode.type === 'category'
                        ? 'bg-[#132c22] text-[#34d399] border-[#1b4332]'
                        : 'bg-[#332712] text-[#fbbf24] border-[#523e1b]'
                    }`}
                  >
                    {selectedNode.type}
                  </span>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div className="bg-[#12141c] border border-[#212635] rounded-lg p-3">
                    <span className="text-[11px] text-slate-400">Documents</span>
                    <div className="text-xl font-bold text-white mt-1">
                      {(selectedNode.document_count || 0).toLocaleString()}
                    </div>
                  </div>
                  <div className="bg-[#12141c] border border-[#212635] rounded-lg p-3">
                    <span className="text-[11px] text-slate-400">Connections</span>
                    <div className="text-xl font-bold text-white mt-1">
                      {selectedNode.connection_count || connectedSemanticNeighbors.length}
                    </div>
                  </div>
                </div>

                {selectedNode.sentiment && (
                  <div className="flex flex-col gap-2">
                    <span className="text-xs font-medium text-slate-300">Sentiment</span>
                    <div className="w-full h-2.5 bg-[#212635] rounded-full overflow-hidden flex">
                      <div
                        className="bg-[#ef4444]"
                        style={{ width: `${selectedNode.sentiment.negative}%` }}
                        title={`Negative: ${selectedNode.sentiment.negative}%`}
                      />
                      <div
                        className="bg-[#64748b]"
                        style={{ width: `${selectedNode.sentiment.neutral}%` }}
                        title={`Neutral: ${selectedNode.sentiment.neutral}%`}
                      />
                      <div
                        className="bg-[#10b981]"
                        style={{ width: `${selectedNode.sentiment.positive}%` }}
                        title={`Positive: ${selectedNode.sentiment.positive}%`}
                      />
                    </div>
                    <span className="text-[11px] text-slate-400">
                      {selectedNode.sentiment.negative}% negative · {selectedNode.sentiment.neutral}% neutral ·{' '}
                      {selectedNode.sentiment.positive}% positive
                    </span>
                  </div>
                )}

                <div className="flex flex-col gap-2.5">
                  <span className="text-xs font-medium text-slate-300">
                    Connected nodes · shared documents
                  </span>
                  <div className="flex flex-col gap-2 max-h-56 overflow-y-auto pr-1">
                    {connectedSemanticNeighbors.length === 0 ? (
                      <span className="text-xs text-slate-500 py-2">No connected nodes found.</span>
                    ) : (
                      connectedSemanticNeighbors.map(({ node: neighbor, sharedDocs }) => {
                        const maxDocs = connectedSemanticNeighbors[0]?.sharedDocs || 1
                        const barPct = Math.round((sharedDocs / maxDocs) * 100)
                        return (
                          <div
                            key={neighbor.id}
                            onClick={() => setSelectedNodeId(neighbor.id)}
                            className="flex flex-col gap-1 cursor-pointer hover:bg-[#1a1e2b] p-1.5 rounded-lg transition-colors"
                          >
                            <div className="flex items-center justify-between text-xs">
                              <div className="flex items-center gap-1.5 truncate max-w-[190px]">
                                <span
                                  className={`w-2 h-2 rounded-full flex-shrink-0 ${
                                    neighbor.type === 'topic'
                                      ? 'bg-[#4f46e5]'
                                      : neighbor.type === 'category'
                                      ? 'bg-[#10b981]'
                                      : 'bg-[#f59e0b]'
                                  }`}
                                />
                                <span className="text-slate-200 truncate">{neighbor.label}</span>
                              </div>
                              <span className="text-slate-400 font-mono text-[11px]">
                                {sharedDocs.toLocaleString()}
                              </span>
                            </div>
                            <div className="w-full h-1 bg-[#212635] rounded-full overflow-hidden">
                              <div
                                className="h-full bg-[#4f6bf5] rounded-full"
                                style={{ width: `${barPct}%` }}
                              />
                            </div>
                          </div>
                        )
                      })
                    )}
                  </div>
                </div>

                <div className="pt-2">
                  <button
                    onClick={() => {
                      setDocPage(1)
                      setIsDocModalOpen(true)
                    }}
                    className="w-full py-2.5 bg-[#252a36] hover:bg-[#2f3544] text-slate-200 hover:text-white text-xs font-medium rounded-lg transition-colors"
                  >
                    View documents
                  </button>
                </div>
              </div>
            )
          ) : (
            !selectedNode ? (
              <div className="flex flex-col gap-2">
                <h3 className="text-sm font-semibold text-white">Details</h3>
                <p className="text-xs text-slate-400 leading-relaxed">
                  Select a node in the lineage graph to inspect users, datasets, models, predictions or
                  feedback.
                </p>
              </div>
            ) : selectedNode.type === 'model' ? (
              <div className="flex flex-col gap-5">
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <h3 className="text-base font-bold text-white tracking-tight">
                      {selectedNode.name || 'Model'} {selectedNode.label}
                    </h3>
                    <p className="text-xs text-slate-400 mt-0.5">
                      {selectedNode.algorithm} · {selectedNode.feature_type} features
                    </p>
                  </div>
                  {selectedNode.deployed && (
                    <span className="text-[11px] font-medium px-2 py-0.5 rounded-full bg-[#132c22] text-[#34d399] border border-[#1b4332]">
                      Deployed
                    </span>
                  )}
                </div>

                <div className="grid grid-cols-2 gap-2.5">
                  <div className="bg-[#12141c] border border-[#212635] rounded-lg p-3">
                    <span className="text-[11px] text-slate-400">F1</span>
                    <div className="text-xl font-bold text-white mt-1">
                      {selectedNode.f1 !== null && selectedNode.f1 !== undefined
                        ? selectedNode.f1.toFixed(2)
                        : '—'}
                    </div>
                    <span
                      className={`text-[10px] block mt-1 ${
                        selectedNode.f1 && selectedNode.f1 >= 0.85 ? 'text-[#34d399]' : 'text-slate-500'
                      }`}
                    >
                      {selectedNode.f1 && selectedNode.f1 >= 0.85 ? 'Target 0.85 met' : 'Target 0.85'}
                    </span>
                  </div>

                  <div className="bg-[#12141c] border border-[#212635] rounded-lg p-3">
                    <span className="text-[11px] text-slate-400">Accuracy</span>
                    <div className="text-xl font-bold text-white mt-1">
                      {selectedNode.accuracy !== null && selectedNode.accuracy !== undefined
                        ? selectedNode.accuracy.toFixed(2)
                        : '—'}
                    </div>
                  </div>

                  <div className="bg-[#12141c] border border-[#212635] rounded-lg p-3">
                    <span className="text-[11px] text-slate-400">Precision</span>
                    <div className="text-xl font-bold text-white mt-1">
                      {selectedNode.precision !== null && selectedNode.precision !== undefined
                        ? selectedNode.precision.toFixed(2)
                        : '—'}
                    </div>
                  </div>

                  <div className="bg-[#12141c] border border-[#212635] rounded-lg p-3">
                    <span className="text-[11px] text-slate-400">Recall</span>
                    <div className="text-xl font-bold text-white mt-1">
                      {selectedNode.recall !== null && selectedNode.recall !== undefined
                        ? selectedNode.recall.toFixed(2)
                        : '—'}
                    </div>
                  </div>
                </div>

                <div className="flex flex-col gap-2.5 text-xs">
                  <div className="flex justify-between py-1 border-b border-[#212635]">
                    <span className="text-slate-400">Trained on</span>
                    <span className="text-slate-200 font-medium">{selectedNode.trained_on || 'Dataset'}</span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-[#212635]">
                    <span className="text-slate-400">Created by</span>
                    <span className="text-slate-200 font-medium">{selectedNode.created_by || 'Admin'}</span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-[#212635]">
                    <span className="text-slate-400">Status</span>
                    <span className="text-slate-200 font-medium capitalize">{selectedNode.status || 'trained'}</span>
                  </div>
                </div>

                <div className="pt-2">
                  <button
                    onClick={() => {
                      const mId = selectedNode.model_id || selectedNode.id.replace('model_', '')
                      navigate(`/models/evaluate?id=${mId}`)
                    }}
                    className="w-full py-2.5 bg-[#4f6bf5] hover:bg-[#4159d4] text-white text-xs font-medium rounded-lg transition-colors flex items-center justify-center gap-2"
                  >
                    <span>Open evaluation</span>
                    <ExternalLink size={14} />
                  </button>
                </div>
              </div>
            ) : (
              <div className="flex flex-col gap-4">
                <div className="flex items-start justify-between">
                  <h3 className="text-base font-bold text-white">{selectedNode.label}</h3>
                  <span className="text-[11px] font-medium px-2 py-0.5 rounded-full bg-[#1e244a] text-[#818cf8] capitalize border border-[#374174]">
                    {selectedNode.type}
                  </span>
                </div>
                {selectedNode.type === 'dataset' && (
                  <div className="flex flex-col gap-2 text-xs">
                    <div className="flex justify-between py-1 border-b border-[#212635]">
                      <span className="text-slate-400">Rows</span>
                      <span className="text-slate-200 font-mono">
                        {(selectedNode.row_count || 0).toLocaleString()}
                      </span>
                    </div>
                    <div className="flex justify-between py-1 border-b border-[#212635]">
                      <span className="text-slate-400">Source</span>
                      <span className="text-slate-200 capitalize">{selectedNode.source || 'upload'}</span>
                    </div>
                  </div>
                )}
                {selectedNode.type === 'user' && (
                  <div className="flex flex-col gap-2 text-xs">
                    <div className="flex justify-between py-1 border-b border-[#212635]">
                      <span className="text-slate-400">Email</span>
                      <span className="text-slate-200 font-mono">{selectedNode.email}</span>
                    </div>
                    <div className="flex justify-between py-1 border-b border-[#212635]">
                      <span className="text-slate-400">Role</span>
                      <span className="text-slate-200 capitalize">{selectedNode.role}</span>
                    </div>
                  </div>
                )}
                {(selectedNode.type === 'prediction' || selectedNode.type === 'feedback') && (
                  <div className="flex flex-col gap-2 text-xs">
                    <div className="flex justify-between py-1 border-b border-[#212635]">
                      <span className="text-slate-400">Volume</span>
                      <span className="text-slate-200 font-mono">
                        {(selectedNode.count || 0).toLocaleString()}
                      </span>
                    </div>
                  </div>
                )}
              </div>
            )
          )}
        </div>
      </div>

      {isDocModalOpen && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-[#161922] border border-[#252a36] rounded-2xl w-full max-w-2xl max-h-[85vh] flex flex-col shadow-2xl overflow-hidden">
            <div className="p-5 border-b border-[#212635] flex items-center justify-between">
              <div>
                <h3 className="text-sm font-semibold text-white">
                  Documents for "{selectedNode?.label}"
                </h3>
                <span className="text-[11px] text-slate-400 capitalize">
                  {selectedNode?.type} · {nodeDocsData?.total || 0} matching documents
                </span>
              </div>
              <button
                onClick={() => setIsDocModalOpen(false)}
                className="text-slate-400 hover:text-white p-1 rounded-lg hover:bg-[#252a36] transition-colors"
              >
                <X size={18} />
              </button>
            </div>

            <div className="p-5 overflow-y-auto flex-1 flex flex-col gap-3">
              {isNodeDocsLoading ? (
                <div className="py-16 text-center text-xs text-slate-400">Loading snippets...</div>
              ) : !nodeDocsData || nodeDocsData.documents.length === 0 ? (
                <div className="py-16 text-center text-xs text-slate-400">No documents found.</div>
              ) : (
                nodeDocsData.documents.map((doc: any) => (
                  <div
                    key={doc.id}
                    className="p-3.5 bg-[#12141c] border border-[#212635] rounded-xl flex flex-col gap-2"
                  >
                    <p className="text-xs text-slate-200 leading-relaxed">{doc.snippet}</p>
                    <div className="flex items-center gap-2 flex-wrap text-[11px]">
                      {doc.label && (
                        <span className="px-2 py-0.5 rounded bg-[#132c22] text-[#34d399] border border-[#1b4332]">
                          {doc.label}
                        </span>
                      )}
                      {doc.sentiment && (
                        <span
                          className={`px-2 py-0.5 rounded border ${
                            doc.sentiment === 'Positive'
                              ? 'bg-[#132c22] text-[#34d399] border-[#1b4332]'
                              : doc.sentiment === 'Negative'
                              ? 'bg-[#33181b] text-[#f87171] border-[#53262b]'
                              : 'bg-[#1e2338] text-slate-300 border-[#2b334e]'
                          }`}
                        >
                          {doc.sentiment}
                        </span>
                      )}
                      {doc.confidence !== null && (
                        <span className="text-slate-400 font-mono">{doc.confidence}%</span>
                      )}
                      {doc.timestamp && <span className="text-slate-500 font-mono ml-auto">{doc.timestamp}</span>}
                    </div>
                  </div>
                ))
              )}
            </div>

            {nodeDocsData && nodeDocsData.total > 8 && (
              <div className="p-4 border-t border-[#212635] flex items-center justify-between text-xs text-slate-400 bg-[#141720]">
                <span>
                  Page {docPage} of {Math.ceil(nodeDocsData.total / 8)}
                </span>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => setDocPage((p) => Math.max(1, p - 1))}
                    disabled={docPage === 1}
                    className="px-3 py-1 bg-[#191c25] border border-[#252a36] rounded text-slate-300 disabled:opacity-40 flex items-center gap-1 hover:bg-[#252a36]"
                  >
                    <ChevronLeft size={14} />
                    <span>Previous</span>
                  </button>
                  <button
                    onClick={() => setDocPage((p) => p + 1)}
                    disabled={docPage * 8 >= nodeDocsData.total}
                    className="px-3 py-1 bg-[#191c25] border border-[#252a36] rounded text-slate-300 disabled:opacity-40 flex items-center gap-1 hover:bg-[#252a36]"
                  >
                    <span>Next</span>
                    <ChevronRight size={14} />
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
