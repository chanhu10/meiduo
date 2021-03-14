var vm = new Vue({
    el:"#app",
    delimiters: ["[[", "]]"],
    data : {
        // v-model
        username:'',
        password:'',
        password2:'',
        mobile:'',
        allow:'',
        image_code_url:'',
        uuid:'',
        image_code:'',
        sms_code:'',
        sms_code_tip:'获取短信验证码',
        send_flag:false,



        // v-show
        error_name: false,
        error_password: false,
        error_password2: false,
        error_mobile: false,
        error_allow: false,
        error_image_code: false,
        error_sms_code:false,

        // error_message
        error_name_message:'',
        error_mobile_message:'',
        error_image_code_msg:'',
        error_sms_code_msg:'',

    },
    mounted(){//页面加载完调用
        //生成图形验证码
        this.generate_image_code();

        },


    methods:{
        generate_image_code(){
            this.uuid = generateUUID();
            this.image_code_url = "/image_codes/"+this.uuid;

        },
        check_username(){
            let re = /^[0-9a-zA-Z_-]{5,20}$/;
            if(re.test(this.username)){
                this.error_name = false;
            }else{
                this.error_name = true;
                this.error_name_message = "请输入5-20个字符的用户名";
            }
            if(this.error_name === false){
                let url = 'usernames/' + this.username + '/count'
                axios.get(url,{
                    responseType:'json'})
                    .then(response=>{if(response.data.count === 1){
                        this.error_name_message = "用户已注册";
                        this.error_name = true;
                    }else{
                        this.error_name = false;
                    }
                    })
                    .catch(error=>{console.log(error.response);
                    })

            }


        },

        check_password(){
            let re = /^[0-9a-zA-Z]{8,20}$/;
            if(re.test(this.password)){
                this.error_password = false;
            }else{
                this.error_password = true;

            }
        },
        check_password2(){
            if(this.password !== this.password2){
                this.error_password2 = true;

            }else{
                this.error_password2 = false;
            }
        },
        check_mobile(){
            let re = /^1[3-9]\d{9}$/;
            if(re.test(this.mobile)){
                this.error_mobile = false;
            }else {
                this.error_mobile = true;
                this.error_mobile_message = "您输入的手机号格式不正确";

            }
        },
        check_image_code(){
            if(this.image_code.length !== 4){
                this.error_image_code_msg = "请输入正确的图形验证码";
                this.error_image_code = true;
            }else{
                this.error_image_code = false;
            }
        },
        send_msg_code(){
            if(this.send_flag === true){

                return;
            }
            this.send_flag = true;
            this.check_mobile();
            this.check_image_code();
            if (this.error_mobile == true || this.error_image_code == true){
                this.send_flag = false;
                return;
            }

            let url = "sms_codes/"+this.mobile+"/?image_code="+this.image_code+"&uuid="+this.uuid
            axios.get(url, {
                responseType:"json"
            })
                .then(response => {
                    if (response.data.code === '0'){
                        //展示倒计时60秒的效果
                        var num = 60;
                        var t = setInterval(() => {
                            if (num === 1){
                                clearInterval(t);
                                this.sms_code_tip = '获取短信验证码';
                                this.generate_image_code();
                                this.send_flag = false;

                            }else {
                                num -= 1;
                                this.sms_code_tip = num + "秒";
                            }
                        }, 1000)
                    } else{
                        if(response.data.code === '4001'){
                            this.error_image_code_msg = response.data.errmsg;
                            this.error_image_code = true;
                        //图形验证码错误
                        }else{//4002
                            this.error_sms_code_msg = response.data.errmsg;
                            this.error_sms_code = true;
                        }
                        this.send_flag = false;
                    }

                })
                .catch(error=>{
                    console.log(error.response);
                    this.send_flag = false;
                }
                )

        },
        check_sms_code(){
            if(this.sms_code.length !== 6){
                this.error_sms_code_msg = "请输入正确的短信验证码";
                this.error_sms_code = true;

            }else{
                this.error_sms_code = false;
            }
        },

        check_allow(){
            if(!this.allow){
                this.error_allow = true;
            }else{
                this.error_allow = false;
            }
        },
        on_submit(){
            this.check_username();
            this.check_password();
            this.check_password2();
            this.check_mobile();
            this.check_sms_code();
            this.check_allow();

            if(this.error_name === true || this.error_password===true || this.error_password2===true
            || this.error_mobile===true ||this.error_sms_code===true|| this.error_allow===true){
                window.event.returnValue = false
            }
        },


    }

})