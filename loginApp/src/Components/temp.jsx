import { useState } from "react";

const InputField = ({type, placeholder, icon, value, onChange}) => {

    const [isVisible, setVisible] =useState(false);
    return (
        
            <div className="input-wrapper">
                <input type={isVisible ?  'text': type} placeholder={placeholder} className="input-field" required
                value={value} onChange={onChange} />
                <i className="material-symbols-outlined">{icon}</i>

                {type === "password" && (
                <i  onClick = {() => setVisible(prevState => !prevState)}className="material-symbols-outlined eye-icon">
                    {isVisible ? 'visibility' : 'visibility_off'}</i>

                )}
            </div>
        

    );

};

export default InputField;