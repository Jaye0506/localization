import streamlit as st

class OptionList:
    counter = 0
    def __init__(self, options:list,label='下拉选项',options_list_num=None) -> None:
        self.bind_state = f'state_opts_list_{options_list_num}'
        self.label = label
        self.counter+=1
        self.options = None
        self.switch = None
        self.set_options(options, options_list_num)
        
    def set_options(self,opts, options_list_num):
        self.options = []
        if isinstance(opts,list) and len(opts)>0:
            with st.expander(self.label):
                if self.bind_state not in st.session_state:
                    st.session_state[self.bind_state] = False
                self.switch = st.toggle('全选', on_change=self.handle_change,key=f'OptionList_toggle_{opts[0]}_{options_list_num}')
                for i,o in enumerate(opts):
                    if isinstance(o, int):
                        o = str(o)
                    self.options.append((i,o,st.checkbox(o,st.session_state[self.bind_state],key=self.bind_state+f'_{o}_{options_list_num}')))
                # _, col2 = st.columns([0.85,0.15])
                # with col2:
                
    def handle_change(self):
        if self.switch:
            st.session_state[self.bind_state]=False
        else:
            st.session_state[self.bind_state]=True

# op_list = OptionList(['a','b','c'])
# print(op_list.options)
# op_list.set_options(['haha','cool','gogogo'])
# st.multiselect('选择',['a','b','c'])


