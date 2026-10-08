from pathlib import Path
import shutil
import tkinter as tk
from tkinter import filedialog,messagebox,ttk
from voice_mixer.demo import create_demo
from voice_mixer.storage import load_library
from voice_mixer.planner import plan_sentence
from voice_mixer.audio import AudioSegment, render_plan

ROOT=Path(__file__).resolve().parent; LIB=ROOT/'data/library.json'; OUT=ROOT/'output/gui_result.wav'

class App:
    def __init__(self,root):
        self.root=root; self.root.title('Flowery Sentence Mixer Demo'); self.root.geometry('1050x680'); self.fragments=[]; self.plan=None; self.latest_output=OUT if OUT.is_file() else None
        top=ttk.Frame(root,padding=12); top.pack(fill='x'); ttk.Label(top,text='Flowery Sentence Mixer Demo',font=('TkDefaultFont',20,'bold')).pack(anchor='w'); ttk.Label(top,text='Made by Matthew').pack(anchor='w')
        controls=ttk.Frame(root,padding=(12,8)); controls.pack(fill='x'); ttk.Button(controls,text='Create Demo Library',command=self.demo).pack(side='left'); ttk.Button(controls,text='Reload Library',command=self.load).pack(side='left',padx=6)
        self.target=tk.StringVar(value="Your dad's falling!"); ttk.Entry(controls,textvariable=self.target,font=('TkDefaultFont',12)).pack(side='left',fill='x',expand=True,padx=8); ttk.Button(controls,text='BUILD',command=self.build).pack(side='left'); self.status=tk.StringVar(); ttk.Label(root,textvariable=self.status,padding=(12,0)).pack(anchor='w')
        audio_controls=ttk.Frame(root,padding=(12,6)); audio_controls.pack(fill='x')
        self.play_button=ttk.Button(audio_controls,text='Play latest audio',command=self.play_latest); self.play_button.pack(side='left')
        self.stop_button=ttk.Button(audio_controls,text='Stop',command=self.stop_latest); self.stop_button.pack(side='left',padx=6)
        self.save_wav_button=ttk.Button(audio_controls,text='Save WAV as…',command=self.save_latest_wav); self.save_wav_button.pack(side='left')
        self.save_mp3_button=ttk.Button(audio_controls,text='Save MP3 as…',command=self.save_latest_mp3); self.save_mp3_button.pack(side='left',padx=6)
        self.latest_label=tk.StringVar(); ttk.Label(audio_controls,textvariable=self.latest_label).pack(side='left',padx=10)
        self._refresh_output_controls(); self.root.protocol('WM_DELETE_WINDOW',self.close)
        pane=ttk.PanedWindow(root,orient='horizontal'); pane.pack(fill='both',expand=True,padx=12,pady=8); left=ttk.Frame(pane,padding=8); right=ttk.Frame(pane,padding=8); pane.add(left,weight=1); pane.add(right,weight=2)
        ttk.Label(left,text='Library').pack(anchor='w'); self.tree=ttk.Treeview(left,columns=('kind','text','dur'),show='headings');
        for c,h,w in [('kind','Kind',80),('text','Text',190),('dur','Seconds',80)]: self.tree.heading(c,text=h); self.tree.column(c,width=w)
        self.tree.pack(fill='both',expand=True); ttk.Label(right,text='Assembly plan').pack(anchor='w'); self.out=tk.Text(right,wrap='word'); self.out.pack(fill='both',expand=True); self.load()
    def demo(self):
        demo_library=create_demo(ROOT)
        self.load(demo_library)
        messagebox.showinfo('Demo ready','Demo library created separately. Your recordings library is unchanged.')
    def load(self,path=LIB):
        self.fragments=load_library(path); self.tree.delete(*self.tree.get_children());
        for f in self.fragments:self.tree.insert('','end',values=(f.kind,f.text,f'{f.duration:.2f}'))
        self.status.set(f'{len(self.fragments)} fragments loaded')
    def _refresh_output_controls(self):
        available=self.latest_output is not None and self.latest_output.is_file()
        state='normal' if available else 'disabled'
        self.play_button.configure(state=state); self.stop_button.configure(state=state); self.save_wav_button.configure(state=state); self.save_mp3_button.configure(state=state)
        label=f'Latest audio: {self.latest_output.relative_to(ROOT)}' if available else 'Latest audio: not built yet'
        self.latest_label.set(label)
    def play_latest(self):
        if self.latest_output is None or not self.latest_output.is_file():return
        try:
            import winsound
            winsound.PlaySound(str(self.latest_output),winsound.SND_FILENAME|winsound.SND_ASYNC)
            self.status.set(f'Playing {self.latest_output.name}')
        except Exception as e:messagebox.showerror('Playback unavailable',str(e),parent=self.root)
    def stop_latest(self):
        try:
            import winsound
            winsound.PlaySound(None,0)
            self.status.set('Playback stopped')
        except (ImportError,RuntimeError):pass
    def _save_dialog(self,extension,description):
        return filedialog.asksaveasfilename(parent=self.root,title=f'Save latest audio as {extension.upper()}',initialdir=str(self.latest_output.parent),initialfile=f'{self.latest_output.stem}.{extension}',defaultextension=f'.{extension}',filetypes=[(description,f'*.{extension}')])
    def save_latest_wav(self):
        if self.latest_output is None or not self.latest_output.is_file():return
        destination=self._save_dialog('wav','WAV audio')
        if not destination:return
        try:
            target=Path(destination)
            if target.resolve()!=self.latest_output.resolve():shutil.copy2(self.latest_output,target)
            self.status.set(f'Saved audio to {target}')
            messagebox.showinfo('Audio saved',f'Saved the latest audio to:\n{target}',parent=self.root)
        except Exception as e:messagebox.showerror('Save failed',str(e),parent=self.root)
    def save_latest_mp3(self):
        if self.latest_output is None or not self.latest_output.is_file():return
        destination=self._save_dialog('mp3','MP3 audio')
        if not destination:return
        try:
            ffmpeg=ROOT/'.venv'/'Scripts'/'ffmpeg.exe'
            if ffmpeg.is_file():AudioSegment.converter=str(ffmpeg)
            target=Path(destination)
            AudioSegment.from_wav(self.latest_output).export(target,format='mp3',bitrate='192k')
            self.status.set(f'Saved MP3 to {target}')
            messagebox.showinfo('Audio saved',f'Saved the latest audio as MP3 to:\n{target}',parent=self.root)
        except Exception as e:messagebox.showerror('MP3 export failed',str(e),parent=self.root)
    def close(self):
        self.stop_latest(); self.root.destroy()
    def build(self):
        if not self.fragments:self.demo(); return
        self.stop_latest()
        self.plan=plan_sentence(self.target.get(),self.fragments); self.out.delete('1.0','end'); self.out.insert('end',f'TARGET: {self.plan.target}\nSCORE: {self.plan.total_score:.1f}\n\n')
        for i,s in enumerate(self.plan.steps,1):
            self.out.insert('end',f'{i}. {s.target_text}\n   reason: {s.reason}\n   score: {s.score:.1f}\n')
            if s.audio_fragments:
                if len(s.audio_fragments) == 1:
                    f=s.audio_fragments[0]; self.out.insert('end',f'   source: {Path(f.source).name}\n   time: {f.start:.3f} → {f.end:.3f}\n   phones: {" ".join(f.phones) or "(not indexed)"}\n\n')
                else:
                    labels=' '.join(f.phones[0] if f.phones else f.text for f in s.audio_fragments)
                    self.out.insert('end',f'   phoneme pieces: {labels}\n')
                    for f in s.audio_fragments:self.out.insert('end',f'   {Path(f.source).name} [{f.start:.3f} → {f.end:.3f}] {f.phones[0] if f.phones else f.text}\n')
                    self.out.insert('end','\n')
            else:self.out.insert('end','   MISSING: no generation.\n\n')
        try:
            render_plan(self.plan,OUT); self.latest_output=OUT; self._refresh_output_controls(); self.out.insert('end',f'RENDERED: {OUT}\n'); self.status.set('Audio ready — play it or save as WAV/MP3')
        except Exception as e:self.out.insert('end',f'RENDER UNAVAILABLE: {e}\n'); self.status.set('Audio could not be rendered')

if __name__=='__main__':
    r=tk.Tk(); App(r); r.mainloop()
