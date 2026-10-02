import com.uppaal.engine.Engine;
import com.uppaal.engine.connection.LocalConnection;
import com.uppaal.model.io2.Problem;
import com.uppaal.model.system.*;
import com.uppaal.model.system.symbolic.*;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;
import java.util.concurrent.TimeUnit;

/** Bounded witness selection and independent replay on the full changed-model candidate. */
public final class CausalReplay {
    static Engine engine; static UppaalSystem sys; static Path out;
    static PrintWriter log; static long started; static int nodes, failed;
    static List<SymbolicTransition> best=List.of();
    static Map<String,Object> report=new LinkedHashMap<>();
    static void require(boolean b,String s) { TimedReplay.require(b,s); }
    static int value(SymbolicState s,String n) { return s.getVariableValues()[TimedReplay.index(sys,n,false)]; }
    static boolean goal(SymbolicState s) {
        return s.getLocationVector()[16].getName().equals("Completed")
            && value(s,"c82_success")==1 && value(s,"c82_received")==1
            && value(s,"c82_admitted")==1 && value(s,"c82_sampled")==1
            && value(s,"c82_enqueued")==1 && value(s,"c82_dispatched")==1
            && value(s,"c82_attempted")==1 && value(s,"c82_outcome")==1
            && value(s,"c82_received_request_id")==1 && value(s,"c82_received_sample_id")==1
            && value(s,"c82_receipt_timely")==1 && value(s,"c82_receipt_quality")==1;
    }
    static Map<String,Object> snapshot(SymbolicState s) {
        Map<String,Object> m=new LinkedHashMap<>();
        List<String> loc=new ArrayList<>();for(SystemLocation l:s.getLocationVector())loc.add(l.getName());
        m.put("locations",loc);m.put("values",s.getVariableValues());
        m.put("zone",TimedReplay.matrix(sys.getNoOfClocks(),TimedReplay.raw(s.getPolyhedron())));
        m.put("goal",goal(s));return m;
    }
    static void emit(Map<String,Object> e) { TimedReplay.event(log,e); }
    static void budget() {
        require((System.nanoTime()-started)/1e9<55,"cell wall limit");
        require(nodes<=256 && failed<=64,"node/branch limit");
    }
    static boolean matches(String key,int[] spec) {
        String[] p=key.split(";")[0].trim().split("\\s+");
        if(Integer.parseInt(p[0])!=spec[0])return false;
        int edge=Integer.parseInt(p[1]);
        if(spec[1]==-1) return edge>=56 && edge<=59; // aggregate KPI report, mode-derived
        if(edge!=spec[1] || p.length!=spec.length)return false;
        for(int i=2;i<p.length;i++)if(Integer.parseInt(p[i])!=spec[i])return false;
        return true;
    }
    static boolean search(SymbolicState state,List<int[]> spine,int at,List<SymbolicTransition> path) throws Exception {
        budget();nodes++;
        if(path.size()>best.size()) { best=new ArrayList<>(path);TimedReplay.savePath(out.resolve("partial.xtr"),best); }
        if(at==spine.size()) {
            emit(new LinkedHashMap<>(Map.of("node",nodes,"waypoint",at,"snapshot",snapshot(state))));
            return goal(state);
        }
        require(path.size()<=128,"path step limit");
        List<SymbolicTransition> choices=engine.getTransitions(sys,state).get(20,TimeUnit.SECONDS);
        List<SymbolicTransition> selected=new ArrayList<>();List<String> enabled=new ArrayList<>();
        for(SymbolicTransition t:choices) {
            if(t.getTarget()==null || !t.hasEdges())continue;
            String k=TimedReplay.edgeKey(t);enabled.add(k);
            if(matches(k,spine.get(at)))selected.add(t);
        }
        boolean maintenance=false;
        if(selected.isEmpty()) {
            // B_KPI's inherited p/m invariants require these idle timer resets
            // every abstract unit even when no notification is pending.
            for(SymbolicTransition t:choices) {
                if(t.getTarget()==null || !t.hasEdges())continue;
                String[] key=TimedReplay.edgeKey(t).split(";")[0].trim().split("\\s+");
                int process=Integer.parseInt(key[0]),edge=Integer.parseInt(key[1]);
                if(process==27 && Set.of(52,55,58,61,64,67).contains(edge)) {
                    selected.add(t);maintenance=true;break;
                }
            }
        }
        emit(new LinkedHashMap<>(Map.of("node",nodes,"waypoint",at,"depth",path.size()-1,
            "preferred",spine.get(at),"enabled_edges",enabled,"matching",selected.size(),"maintenance",maintenance,"snapshot",snapshot(state))));
        int n=0;
        for(SymbolicTransition choice:selected) {
            if(n++==4)break;
            path.add(choice);
            if(search(choice.getTarget(),spine,maintenance?at:at+1,path))return true;
            path.remove(path.size()-1);failed++;budget();
        }
        return false;
    }
    static void replay(Path traceFile,String mode) throws Exception {
        TimedReplay.Trace trace=new TimedReplay.Parser(Files.readString(traceFile)).parse(sys.getNoOfProcesses(),sys.getNoOfVariables(),sys.getNoOfClocks());
        report.put("trace_hash",TimedReplay.hash(traceFile));
        List<TimedReplay.Stored> saved=new ArrayList<>(trace.states());int last=saved.size()-1;
        if(mode.equals("negative-discrete")) {
            var s=saved.get(last);int[] v=s.values().clone();v[TimedReplay.index(sys,"c82_received_sample_id",false)]=0;
            saved.set(last,new TimedReplay.Stored(s.locations(),v,s.bounds()));
        }
        if(mode.equals("negative-clock")) {
            var s=saved.get(last);int c=TimedReplay.index(sys,"c82_measure_age",true);
            saved.set(last,new TimedReplay.Stored(s.locations(),s.values(),List.of(new int[]{0,c,1},new int[]{c,0,1})));
        }
        SymbolicState initial=engine.getInitialState(sys).get(10,TimeUnit.SECONDS);
        require(TimedReplay.discreteMatch(initial,saved.get(0)),"initial vector mismatch");
        int nc=sys.getNoOfClocks();int[][] z=TimedReplay.intersection(TimedReplay.matrix(nc,TimedReplay.raw(initial.getPolyhedron())),TimedReplay.matrix(nc,saved.get(0).bounds()));
        require(z!=null,"initial zone mismatch");SymbolicState first=TimedReplay.restrict(sys,initial,z);
        List<TimedReplay.Reach> frontier=List.of(new TimedReplay.Reach(first,List.of(new SymbolicTransition(null,null,first))));
        emit(new LinkedHashMap<>(Map.of("state_index",0,"snapshot",snapshot(first))));
        int accepted=0;
        for(int step=1;step<=last;step++) {
            budget();var target=saved.get(step);int[][] tz=TimedReplay.matrix(nc,target.bounds());require(tz!=null,"empty input DBM");
            List<TimedReplay.Reach> next=new ArrayList<>();int edges=0,discrete=0;
            for(var reach:frontier)for(var choice:engine.getTransitions(sys,reach.state()).get(20,TimeUnit.SECONDS)) {
                if(choice.getTarget()==null || !choice.hasEdges() || !TimedReplay.edgeKey(choice).equals(trace.edges().get(step-1)))continue;
                edges++;if(!TimedReplay.discreteMatch(choice.getTarget(),target))continue;discrete++;
                int[][] common=TimedReplay.intersection(TimedReplay.matrix(nc,TimedReplay.raw(choice.getTarget().getPolyhedron())),tz);
                if(common==null)continue;SymbolicState restricted=TimedReplay.restrict(sys,choice.getTarget(),common);
                List<SymbolicTransition> path=new ArrayList<>(reach.path());path.add(new SymbolicTransition(reach.state(),choice.getEdges(),restricted));
                next.add(new TimedReplay.Reach(restricted,path));
            }
            if(next.isEmpty()) {
                String reason=edges==0?"edge_not_enabled":discrete==0?"discrete_state_mismatch":"clock_zone_disjoint";
                report.put("status","rejected");report.put("reason",reason);report.put("first_unavailable_state_index",step);
                report.put("control_expected_rejection",!mode.equals("replay") && step==last && reason.equals(mode.equals("negative-clock")?"clock_zone_disjoint":"discrete_state_mismatch"));
                best=frontier.get(0).path();break;
            }
            require(next.size()<=8,"frontier cap");frontier=next;accepted=step;best=frontier.get(0).path();
            emit(new LinkedHashMap<>(Map.of("state_index",step,"edges",trace.edges().get(step-1),"edge_matches",edges,"discrete_matches",discrete,"frontier",next.size(),"snapshot",snapshot(frontier.get(0).state()))));
            if(step==last) { require(goal(frontier.get(0).state()),"endpoint predicate absent");report.put("status","replay_complete");report.put("goal",true); }
        }
        report.put("accepted_transitions",accepted);report.put("stored_states",saved.size());
        TimedReplay.savePath(out.resolve("reachable-prefix.xtr"),best);
    }
    public static void main(String[] args) {
        int exit=2;LocalConnection connection=null;started=System.nanoTime();
        try {
            if(args.length==2 && args[0].equals("--model-check")) {
                var doc=TimedReplay.loadModel(Path.of(args[1]));
                require(doc.getTemplateList().size()==51,"loader lost a template");
                require(doc.getPropertyValue("system").toString().contains("c82_job"),"loader lost system");
                System.out.println("51 templates and candidate system loaded; engine not invoked");return;
            }
            require(args.length==6,"SERVER MODEL SPINE_OR_TRACE OUTPUT MODE MODEL_HASH");
            Path model=Path.of(args[1]),input=Path.of(args[2]);out=Path.of(args[3]);String mode=args[4];
            String modelHash=TimedReplay.hash(model); require(modelHash.equals(args[5]),"model hash drift");
            Files.createDirectories(out);log=new PrintWriter(Files.newBufferedWriter(out.resolve("steps.jsonl"),StandardCharsets.UTF_8));
            report.put("mode",mode);report.put("model_hash",modelHash);report.put("input_hash",TimedReplay.hash(input));
            report.put("property_verdict",null);report.put("query_hash",null);
            engine=new Engine();connection=new LocalConnection("c82-local",new File(args[0]));engine.resetConnections(List.of(connection));
            engine.connect().get(10,TimeUnit.SECONDS);report.put("tool_version",engine.getVersion().get(10,TimeUnit.SECONDS));
            ArrayList<Problem> problems=new ArrayList<>();sys=engine.getSystem(TimedReplay.loadModel(model),problems).get(20,TimeUnit.SECONDS);
            for(Problem p:problems)require("warning".equals(p.getType()),"Compilation: "+p);
            report.put("processes",sys.getNoOfProcesses());report.put("variable_names",sys.getVariables());report.put("clock_names",sys.getClockNames());
            if(mode.equals("simulate")) {
                List<int[]> spine=new ArrayList<>();for(String line:Files.readAllLines(input))spine.add(Arrays.stream(line.trim().split("\\s+")).mapToInt(Integer::parseInt).toArray());
                SymbolicState initial=engine.getInitialState(sys).get(10,TimeUnit.SECONDS);List<SymbolicTransition> path=new ArrayList<>(List.of(new SymbolicTransition(null,null,initial)));
                boolean found=search(initial,spine,0,path);report.put("status",found?"goal_reached":"schedule_exhausted");report.put("goal",found);
                report.put("nodes",nodes);report.put("failed_branches",failed);report.put("accepted_transitions",(found?path:best).size()-1);
                TimedReplay.savePath(out.resolve("trace.xtr"),found?path:best);
                report.put("final",snapshot((found?path:best).get((found?path:best).size()-1).getTarget()));
            } else replay(input,mode);
            exit=report.get("status").equals("rejected")?1:report.get("status").equals("schedule_exhausted")?2:0;
        } catch(Exception e) {
            report.put("status","error");report.put("error",e.toString());e.printStackTrace(System.err);
        } finally {
            if(connection!=null)connection.kill();if(log!=null)log.close();
            report.put("elapsed_seconds",(System.nanoTime()-started)/1e9);
            try {if(out!=null)Files.writeString(out.resolve("result.json"),TimedReplay.json(report)+"\n",StandardCharsets.UTF_8);}catch(Exception e){e.printStackTrace();}
        }
        System.out.println(TimedReplay.json(report));System.exit(exit);
    }
}
